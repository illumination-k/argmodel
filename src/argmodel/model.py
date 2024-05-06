import argparse
import logging
from typing import Any, Self, TypedDict, Unpack

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from argmodel.field import get_arg_meta
from argmodel.typing_utils import TypeHintManager

from ._constants import DEFAULT_GROUP

logger = logging.getLogger(__name__)


def _is_none_or_undefined(value: Any) -> bool:
    return value is None or value is PydanticUndefined


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

        if _is_none_or_undefined(default) and self.field.default_factory is not None:
            default = self.field.default_factory()

        return default

    @property
    def help(self) -> str | None:
        if self.field.description is not None and _is_none_or_undefined(self.default):
            return self.field.description

        if self.field.description is None and not _is_none_or_undefined(self.default):
            return f"(default: {self.default})"

        if self.field.description is None and _is_none_or_undefined(self.default):
            return None

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
    def parse_typed_args(
        cls,
        args: list[str] | None = None,
        **kwargs: Unpack[BuildParserKwargs],
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
