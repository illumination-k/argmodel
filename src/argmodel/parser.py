import argparse
import dataclasses
from typing import Callable, Generic, TypeVar

from argmodel.model import ArgModel

BaseArgModel = TypeVar("BaseArgModel", bound=ArgModel)
SubArgModel = TypeVar("SubArgModel", bound=ArgModel)


@dataclasses.dataclass
class SubparserData(Generic[BaseArgModel, SubArgModel]):
    model: type[SubArgModel]
    callback: Callable[[BaseArgModel, SubArgModel], None] | None = None


def get_callback(
    namespace: argparse.Namespace,
) -> Callable[[BaseArgModel, SubArgModel], None] | None:
    assert hasattr(namespace, "subparser_callback")
    return namespace.subparser_callback


def get_subparser_name(namespace: argparse.Namespace) -> str:
    assert hasattr(namespace, "subparser_name")
    return namespace.subparser_name


class Parser(Generic[BaseArgModel]):
    def __init__(self, model: type[BaseArgModel]) -> None:
        self.model = model
        self.subparsers: dict[str, SubparserData] = {}

    def add_subparser(
        self,
        name: str,
        model: type[SubArgModel],
        callback: Callable[[BaseArgModel, SubArgModel], None] | None = None,
    ) -> None:
        self.subparsers[name] = SubparserData(model=model, callback=callback)

    def build_parser(self) -> argparse.ArgumentParser:
        root_parser = self.model.build_parser()
        if len(self.subparsers) == 0:
            return root_parser

        subparsers = root_parser.add_subparsers()
        for name, data in self.subparsers.items():
            subparser_model = data.model
            assert issubclass(subparser_model, ArgModel)

            subparser = subparser_model._build_parser(
                root_parser=subparsers.add_parser(name=name)
            )
            subparser.set_defaults(subparser_name=name)
            subparser.set_defaults(subparser_callback=data.callback)

        return root_parser

    def run_subparsers(self, args: list[str] | None = None) -> None:
        parser = self.build_parser()
        parsed_args = parser.parse_args(args)

        subparser_name = get_subparser_name(parsed_args)
        subparser_callback = get_callback(parsed_args)

        subparser_model = self.subparsers[subparser_name].model

        if subparser_callback is not None:
            subparser_callback(
                self.model(**parsed_args.__dict__),
                subparser_model(**parsed_args.__dict__),
            )

    def repr_used_args(self, args: list[str] | None = None) -> list[str]:
        parser = self.build_parser()
        parsed_args = parser.parse_args(args)

        subparser_model = self.subparsers[get_subparser_name(parsed_args)].model

        return (
            self.model(**parsed_args.__dict__).repr_args()
            + subparser_model(**parsed_args.__dict__).repr_args()
        )
