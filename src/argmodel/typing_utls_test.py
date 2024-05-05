from typing import Literal, Optional, Union

from .typing_utils import (
    get_list_inner_type,
    get_literal_values,
    get_optional_inner_type,
    is_literal_type,
    is_optional_type,
    literal_to_union,
)


def test_is_optional_type() -> None:
    assert is_optional_type(str | None) is True
    assert is_optional_type(Optional[str]) is True
    assert is_optional_type(Union[str, int, None]) is True
    assert is_optional_type(Union[str, None]) is True
    assert is_optional_type(str | int | None) is True

    assert is_optional_type(str) is False
    assert is_optional_type(Union[str, int]) is False
    assert is_optional_type(str | int) is False


def test_get_optional_inner_type() -> None:
    assert get_optional_inner_type(str | None) is str
    assert get_optional_inner_type(Optional[str]) is str
    assert get_optional_inner_type(Union[str, int, None]) is Union[str, int]
    assert get_optional_inner_type(Union[str, None]) is str
    assert get_optional_inner_type(str | int | None) is Union[str, int]


def test_get_list_inner_type() -> None:
    assert get_list_inner_type(list[str]) is str
    assert get_list_inner_type(list[int]) is int


def test_is_literal_type() -> None:
    assert is_literal_type(Literal["a", "b", "c"]) is True
    assert is_literal_type(Literal[1, 2, 3]) is True

    assert is_literal_type(str) is False
    assert is_literal_type(int) is False
    assert is_literal_type(Union[str, int]) is False


def test_literal_to_union() -> None:
    assert literal_to_union(Literal["a", "b", "c"]) is str
    assert literal_to_union(Literal[1, 2, 3]) is int
    assert literal_to_union(Literal[1, 2, 3, "a", "b", "c"]) is Union[str, int]


def test_get_literal_values() -> None:
    assert get_literal_values(Literal["a", "b", "c"]) == ("a", "b", "c")
    assert get_literal_values(Literal[1, 2, 3]) == (1, 2, 3)
    assert get_literal_values(Literal[1, 2, 3, "a", "b", "c"]) == (
        1,
        2,
        3,
        "a",
        "b",
        "c",
    )
    assert get_literal_values(Literal[1, 2, 3, "a", "b", "c"]) != (
        1,
        2,
        3,
        "a",
        "b",
        "c",
        "d",
    )
