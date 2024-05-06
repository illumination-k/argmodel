from argmodel import ArgField, ArgModel, Parser
from argmodel.field import LogLevel


class BaseArgs(ArgModel):
    log_level: LogLevel = ArgField(default="INFO", group="logging")


class Subparser1(ArgModel):
    integer: int = ArgField(short="i")
    fp: float = ArgField(short="f")


def subparser1_handler(base: BaseArgs, args: Subparser1) -> None:
    print(base)
    print(args)


class Subparser2(ArgModel):
    store_true: bool = ArgField()
    store_false: bool = ArgField(action="store_false")


def subparser2_handler(base: BaseArgs, args: Subparser2) -> None:
    print(args)
    print(base)


if __name__ == "__main__":
    parser = Parser(model=BaseArgs)
    parser.add_subparser("subparser1", Subparser1, subparser1_handler)
    parser.add_subparser("subparser2", Subparser2, subparser2_handler)
    parser.run_subparsers()
