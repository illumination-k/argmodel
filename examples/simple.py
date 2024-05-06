from typing import Literal

from argmodel import ArgField, ArgModel
from argmodel.field import LogLevel


class ExampleArgs(ArgModel):
    log_level: LogLevel = ArgField(
        default="INFO", group="logging", description="Set the logging level"
    )
    integer: int = ArgField(short="i", group="number")
    fp: float = ArgField(short="f", group="number")
    store_true: bool = ArgField(group="boolean")
    store_false: bool = ArgField(group="boolean", action="store_false")

    list_of_strings: list[str] = ArgField(default=[], nargs="*", group="list")

    choices: Literal["a", "b", "c"] = ArgField(group="choices")


if __name__ == "__main__":
    args = ExampleArgs.parse_typed_args(
        prog="example", description="An example program"
    )
    print(args)
