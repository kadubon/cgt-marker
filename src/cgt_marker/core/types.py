from __future__ import annotations

from typing import TypeAlias

JSONValue: TypeAlias = (
    None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
)
JSONDict: TypeAlias = dict[str, JSONValue]
