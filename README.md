# Argmodel

```python
from typing import Literal

from argmodel import ArgField, ArgModel
from argmodel.field import LogLevel


class ExampleArgs(ArgModel):
    log_level: LogLevel = ArgField(default="INFO", group="logging")
    integer: int = ArgField(short="i", group="number")
    fp: float = ArgField(short="f", group="number")
    store_true: bool = ArgField(group="boolean")
    store_false: bool = ArgField(group="boolean", action="store_false")

    list_of_strings: list[str] = ArgField(default=[], nargs="*", group="list")

    choices: Literal["a", "b", "c"] = ArgField(group="choices")

print(ExampleArgs.parse_args())
```

```
python examples/simple.py -h
usage: simple.py [-h] [--log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--integer INTEGER] [--fp FP] [--store_true] [--store_false] [--list_of_strings [LIST_OF_STRINGS ...]] [--choices {a,b,c}]

options:
  -h, --help            show this help message and exit

logging:
  --log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}

number:
  --integer INTEGER
  --fp FP

boolean:
  --store_true
  --store_false

list:
  --list_of_strings [LIST_OF_STRINGS ...]

choices:
  --choices {a,b,c}
```

```
python examples/simple.py --integer 1 --fp 1.0 --store_true --choices a --list_of_strings 1 23
log_level='INFO' integer=1 fp=1.0 store_true=True store_false=False list_of_strings=['1', '23'] choices='a'
```
