import dataclasses
from typing import Any, Iterable, Literal, TypeAlias, Unpack

from pydantic.fields import FieldInfo, _FieldInfoInputs

Action: TypeAlias = Literal[
    "store_true", "store_false", "store", "store_const", "help", "version"
]
Nargs: TypeAlias = Literal["?", "*", "+"] | int
LogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclasses.dataclass
class ArgMeta:
    group: str = "default"
    short: str | None = None
    nargs: Nargs | None = None
    action: Action | None = None


def get_arg_meta(metadata: Iterable[Any]) -> ArgMeta:
    for meta in metadata:
        if isinstance(meta, ArgMeta):
            return meta

    return ArgMeta()


def ArgField(
    short: str | None = None,
    nargs: Nargs | None = None,
    group: str = "default",
    action: Action | None = None,
    **kwargs: Unpack[_FieldInfoInputs],
) -> Any:
    argmeta = ArgMeta(short=short, nargs=nargs, group=group, action=action)
    field_info = FieldInfo(**kwargs)
    field_info.metadata.append(argmeta)

    return field_info
