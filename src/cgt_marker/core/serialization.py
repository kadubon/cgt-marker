from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from cgt_marker.core.types import JSONValue


def datetime_to_json(value: datetime) -> str:
    return value.isoformat()


def datetime_from_json(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def to_json(data: JSONValue) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def from_json(data: str) -> Any:
    return json.loads(data)
