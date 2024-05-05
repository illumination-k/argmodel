from typing import Literal, Optional

from .field import ArgField
from .model import ArgModel


class SimpleArgs(ArgModel):
    string: str = ArgField(group="group1")
    integer: int = ArgField(group="group1")
    boolean: bool = ArgField(group="group2")
    fp: float = ArgField(group="group2")


def test_simple_args() -> None:
    args = [
        "--string",
        "hello",
        "--integer",
        "42",
        "--boolean",
        "--fp",
        "3.14",
    ]

    parsed = SimpleArgs.parse_args(args)

    assert parsed.string == "hello"
    assert parsed.integer == 42
    assert parsed.boolean is True
    assert parsed.fp == 3.14

    assert sorted(parsed.repr_args()) == sorted(args)


class ListArgs(ArgModel):
    strings: list[str] = ArgField(nargs="*", group="group1")


def test_list_args() -> None:
    args = [
        "--strings",
        "hello",
        "world",
    ]

    parsed = ListArgs.parse_args(args)

    assert parsed.strings == ["hello", "world"]


class OptionalArgs(ArgModel):
    string: str | None = ArgField(default=None, group="group1")
    integer: Optional[int] = ArgField(default=None, group="group1")


def test_optional_args() -> None:
    args = [
        "--string",
        "hello",
        "--integer",
        "42",
    ]

    parsed = OptionalArgs.parse_args(args)

    assert parsed.string == "hello"
    assert parsed.integer == 42

    args = []

    parsed = OptionalArgs.parse_args(args)
    assert parsed.string is None
    assert parsed.integer is None


class LiteralArgs(ArgModel):
    literal: Literal["a", "b", "c"] = ArgField(group="group1")


def test_literal_args() -> None:
    args = [
        "--literal",
        "a",
    ]

    parsed = LiteralArgs.parse_args(args)

    assert parsed.literal == "a"
