import abc
import argparse
import dataclasses
import logging
from typing import ClassVar, Self, TypedDict, Unpack

from pydantic import BaseModel, ValidationError

from argmodel.field import get_arg_meta

from .._constants import DEFAULT_GROUP
from .argument_builder import ArgumentBuilder

logger = logging.getLogger(__name__)


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
    __subparser_data: ClassVar["_SubparserData | None"] = None

    @classmethod
    def add_parsers(cls, dest: str | None = None) -> None:
        cls.__subparser_data = _SubparserData(dest=dest)

    @classmethod
    def add_subparser(cls, name: str, model: "SubParserModel") -> None:
        assert cls.__subparser_data is not None
        cls.__subparser_data.subparsers[name] = model

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

        if cls.__subparser_data is not None:
            subparsers = root_parser.add_subparsers(dest=cls.__subparser_data.dest)

            for name, model in cls.__subparser_data.subparsers.items():
                model._build_parser(subparsers.add_parser(name=name))

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
            return cls.from_namespace(parsed_args)
        except ValidationError as e:
            logger.error(e)
            parser.print_help()
            exit(1)

    @classmethod
    def from_namespace(cls, namespace: argparse.Namespace) -> Self:
        return cls(**vars(namespace))

    @classmethod
    def parse_namespace(cls, namespace: argparse.Namespace) -> None:
        if cls.__subparser_data is None:
            model_instance = cls.from_namespace(namespace)

            if hasattr(model_instance, "callback"):
                model_instance.callback()
        else:
            if not hasattr(namespace, cls.__subparser_data.dest):
                raise ValueError(
                    f"Namespace does not have attribute {cls.__subparser_data.dest}"
                )
            else:
                subparser_name = getattr(namespace, cls.__subparser_data.dest)
                subparser_model = cls.__subparser_data.subparsers[subparser_name]
                subparser_model.parse_namespace(namespace)

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


class SubParserModel(ArgModel, abc.ABC):
    @abc.abstractmethod
    def callback(self) -> None:
        pass


@dataclasses.dataclass
class _SubparserData:
    dest: str | None = None
    subparsers: dict[str, type[SubParserModel]] = dataclasses.field(
        default_factory=dict
    )
