import dataclasses
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from pydantic.types import SecretStr


def is_optional_type(t: Any) -> bool:
    origin = get_origin(t)
    if origin is None:
        return False

    is_union = origin is Union or origin is UnionType
    args = get_args(t)

    return is_union and len([arg for arg in args if arg is type(None)]) == 1


def get_optional_inner_type(t: Any) -> Any:
    assert is_optional_type(t), f"{t} is not an Optional type"
    args = get_args(t)
    types = [arg for arg in args if arg is not type(None)]

    if len(types) == 1:
        return types[0]
    else:
        return Union[tuple(types)]


def get_list_inner_type(t: Any) -> Any:
    origin = get_origin(t)
    args = get_args(t)
    assert origin is list, f"{t} is not a List type"
    return args[0]


def is_literal_type(t: Any) -> bool:
    origin = get_origin(t)

    return origin is Literal


def literal_to_union(t: Any) -> Any:
    assert is_literal_type(t), f"{t} is not a Literal type"
    args = get_args(t)

    types = list(set(type(arg) for arg in args))
    if len(types) == 1:
        return types[0]
    else:
        return Union[tuple(types)]


def get_literal_values(t: Any) -> tuple[Any]:
    assert is_literal_type(t), f"{t} is not a Literal type"
    return get_args(t)


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
