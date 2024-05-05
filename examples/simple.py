from typing import Literal

from argmodel import ArgField, ArgModel
from argmodel.field import LogLevel


class ExampleArgs(ArgModel):
    log_level: LogLevel = ArgField(default="INFO", group="logging")
    integer: int = ArgField(short="i", group="number")
    fp: float = ArgField(short="f", group="number")
    store_true: bool = ArgField(group="boolean")
    store_false: bool = ArgField(group="boolean")

    list_of_strings: list[str] = ArgField(default=[], nargs="*", group="list")

    choices: Literal["a", "b", "c"] = ArgField(group="choices")
    

if __name__ == "__main__":
    args = ExampleArgs.parse_args()
    print(args)