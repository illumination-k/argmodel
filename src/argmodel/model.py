import argparse
from argparse import HelpFormatter
import logging
import dataclasses

from typing import Any, Self, get_origin, TypedDict, Unpack

from pydantic import BaseModel, SecretStr, ValidationError
from pydantic.fields import FieldInfo

from pydantic_core import PydanticUndefined

from argmodel.field import get_arg_meta
from argmodel.typing_utils import (
    get_list_inner_type,
    get_literal_values,
    get_optional_inner_type,
    is_literal_type,
    is_optional_type,
    literal_to_union,
)

from ._constants import DEFAULT_GROUP

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TypeHintManager:
    type_hint: Any
    is_literal: bool = False
    literal_values: tuple[Any] | None = None

    def _unwrap_optional(self) -> None:
        if is_optional_type(self.type_hint):
            self.type_hint = get_optional_inner_type(self.type_hint)

    def _unwrap_literal(self) -> None:
        if is_literal_type(self.type_hint):
            self.is_literal = True
            self.literal_values = get_literal_values(self.type_hint)
            self.type_hint = literal_to_union(self.type_hint)

    def _unwrap_list(self) -> None:
        if get_origin(self.type_hint) is list:
            self.type_hint = get_list_inner_type(self.type_hint)

    def _unwrap_secret(self) -> None:
        if self.type_hint is SecretStr:
            self.type_hint = str

    def unwrap(self) -> Any:
        self._unwrap_optional()
        self._unwrap_list()
        self._unwrap_literal()
        self._unwrap_secret()

        return self.type_hint


class ArgumentBuilder:
    def __init__(self, name: str, field: FieldInfo) -> None:
        self.name = name
        self.field = field
        self.meta = get_arg_meta(field.metadata)
        self.type_hint_manager = TypeHintManager(type_hint=field.annotation)

    @property
    def is_store_true_or_false(self) -> bool:
        return self.meta.action in ["store_true", "store_false"] and self._type is bool

    @property
    def _type(self) -> Any:
        return self.type_hint_manager.unwrap()

    @property
    def choices(self) -> tuple[Any] | None:
        if self.type_hint_manager.is_literal:
            return self.type_hint_manager.literal_values

        return None

    @property
    def default(self) -> Any:
        if self._type is bool:
            return True if self.meta.action == "store_false" else False

        default = self.field.default
        if (
            default is None or default is PydanticUndefined
        ) and self.field.default_factory is not None:
            default = self.field.default_factory()

        return default

    @property
    def help(self) -> str | None:
        if self.field.description is not None and (
            self.default is None or self.default is PydanticUndefined
        ):
            return self.field.description

        if self.field.description is None and (
            self.default is not None and self.default is not PydanticUndefined
        ):
            return f"(default: {self.default})"

        return f"{self.field.description} (default: {self.default})"

    @property
    def args(self) -> list[str]:
        _args = []

        if self.meta.short is not None:
            _args.append(f"-{self.meta.short}")

        _args.append(f"--{self.name}")

        return _args

    @property
    def kwargs(self) -> dict[str, Any]:
        _kwargs: dict[str, Any] = {}

        if not self.is_store_true_or_false:
            _kwargs["metavar"] = self.meta.metavar
            _kwargs["dest"] = self.meta.dest
            _kwargs["choices"] = self.choices
            _kwargs["nargs"] = self.meta.nargs
            _kwargs["type"] = self._type

        _kwargs["help"] = self.help
        _kwargs["default"] = self.default
        _kwargs["action"] = self.meta.action

        return _kwargs


class BuildParserKwargs(TypedDict, total=False):
    prog: str
    usage: str
    description: str
    epilog: str
    formatter_class: HelpFormatter
    prefix_chars: str
    fromfile_prefix_chars: str
    conflict_handler: str
    add_help: bool
    allow_abbrev: bool
    exit_on_error: bool


class ArgModel(BaseModel):
    @classmethod
    def _build_parser(
        cls, root_parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        group: dict[str, list[ArgumentBuilder]] = {}

        for name, field in cls.model_fields.items():
            argument_builder = ArgumentBuilder(name, field)

            group.setdefault(argument_builder.meta.group, []).append(argument_builder)

        for group_name, builders in group.items():
            group_parser: argparse.ArgumentParser | argparse._ArgumentGroup
            if group_name == DEFAULT_GROUP:
                group_parser = root_parser
            else:
                group_parser = root_parser.add_argument_group(group_name)

            for builder in builders:
                group_parser.add_argument(*builder.args, **builder.kwargs)

        return root_parser

    @classmethod
    def build_parser(
        cls, **kwargs: Unpack[BuildParserKwargs]
    ) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(**kwargs)
        cls._build_parser(parser)

        return parser

    @classmethod
    def print_help(cls) -> None:
        cls.build_parser().print_help()

    @classmethod
    def parse_args(
        cls, args: list[str] | None = None, **kwargs: Unpack[BuildParserKwargs]
    ) -> Self:
        parser = cls.build_parser(**kwargs)
        parsed_args = parser.parse_args(args)

        try:
            return cls(**parsed_args.__dict__)
        except ValidationError as e:
            logger.error(e)
            parser.print_help()
            exit(1)

    def repr_args(self) -> list[str]:
        args = []

        field_info = self.model_fields

        for name, value in self.model_dump().items():
            if value is None:
                continue

            if isinstance(value, list):
                args.extend([f"--{name}", *map(str, value)])
            elif isinstance(value, bool):
                argmeta = get_arg_meta(field_info[name].metadata)

                if argmeta.action != "store_false":
                    args.append(f"--{name}")
            else:
                args.extend([f"--{name}", str(value)])

        return args
