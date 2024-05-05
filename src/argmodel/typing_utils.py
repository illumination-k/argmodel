from types import UnionType
from typing import Any, Type, Union, get_args, get_origin


def is_optional_type(t: Any) -> bool:
    origin = get_origin(t)
    if origin is None:
        return False

    is_union = origin is Union or origin is UnionType
    args = get_args(t)

    return is_union and len([arg for arg in args if arg is type(None)]) == 1


def get_optional_inner_type(t: Any) -> Type:
    assert is_optional_type(t), f"{t} is not an Optional type"
    args = get_args(t)
    return [arg for arg in args if arg is not type(None)][0]


def get_list_inner_type(t: Any) -> Type:
    origin = get_origin(t)
    args = get_args(t)
    assert origin is list, f"{t} is not a List type"
    return args[0]
