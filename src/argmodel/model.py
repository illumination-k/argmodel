import argparse
from typing import Any, Self, get_origin

from pydantic import BaseModel, SecretStr

from argmodel.field import get_arg_meta
from argmodel.typing_utils import (
    get_list_inner_type,
    get_literal_values,
    get_optional_inner_type,
    is_literal_type,
    is_optional_type,
    literal_to_union,
)


class ArgModel(BaseModel):
    @classmethod
    def __build_parser(
        cls, root_parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        group: dict[str, list[tuple[list[str], dict[str, Any]]]] = {}

        for name, field in cls.model_fields.items():
            type_hint = field.annotation
            argmeta = get_arg_meta(field.metadata)
            is_literal = False

            if is_optional_type(type_hint):
                type_hint = get_optional_inner_type(type_hint)

            if get_origin(type_hint) is list and (
                argmeta is not None and argmeta.nargs is not None
            ):
                type_hint = get_list_inner_type(type_hint)

            if type_hint is SecretStr:
                type_hint = str

            if is_literal_type(type_hint):
                is_literal = True
                literal_values = get_literal_values(type_hint)
                type_hint = literal_to_union(type_hint)

            argument_args = []
            argument_kwargs: dict[str, Any] = {}

            if type_hint is bool:
                argument_kwargs["action"] = "store_true"
            else:
                argument_kwargs["type"] = type_hint
                if is_literal:
                    argument_kwargs["choices"] = literal_values

                default = field.default
                if default is not None and field.default_factory is not None:
                    default = field.default_factory()
                argument_kwargs["default"] = default

            if argmeta is not None:
                if argmeta.short is not None:
                    argument_args.append(f"-{argmeta.short}")

                if argmeta.action is not None:
                    argument_kwargs["action"] = argmeta.action

                if argmeta.nargs is not None:
                    argument_kwargs["nargs"] = argmeta.nargs

            argument_args.append(f"--{name}")

            group.setdefault(argmeta.group, []).append((argument_args, argument_kwargs))

        for group_name, group_args in group.items():
            if group_name == "default":
                group_parser = root_parser.add_argument_group("default")
            else:
                group_parser = root_parser.add_argument_group(group_name)

            for args, kwargs in group_args:
                group_parser.add_argument(*args, **kwargs)

        return root_parser

    @classmethod
    def build_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        cls.__build_parser(parser)

        return parser

    @classmethod
    def parse_args(cls, args: list[str] | None) -> Self:
        parser = cls.build_parser()
        parsed_args = parser.parse_args(args)

        return cls(**parsed_args.__dict__)

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
