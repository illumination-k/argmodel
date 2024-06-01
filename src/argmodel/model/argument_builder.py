from typing import Any

from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from argmodel.field import get_arg_meta
from argmodel.typing_utils import TypeHintManager


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

        if _is_none_or_undefined(default) and not _is_none_or_undefined(
            self.field.default_factory
        ):
            default = self.field.default_factory()

        return default

    @property
    def help(self) -> str | None:
        help_messages = []

        if self.field.description is not None:
            help_messages.append(self.field.description + ";")

        if self.type_hint_manager.literal_values is not None:
            help_messages.append(f"choices: {', '.join(map(str, self.choices))}")

        if not _is_none_or_undefined(self.default):
            help_messages.append(f"(default: {self.default})")

        return " ".join(help_messages)

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
            _kwargs["required"] = self.field.is_required()

        _kwargs["help"] = self.help
        _kwargs["default"] = self.default
        _kwargs["action"] = self.meta.action

        return _kwargs
