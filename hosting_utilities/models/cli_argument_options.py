from typing import Any, TypedDict


class CLIArgumentOptions(TypedDict, total=False):
    help: str
    required: bool
    type: Any
    default: Any
    choices: list[Any]
    action: str
    metavar: str
    nargs: Any
