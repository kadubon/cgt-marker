from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cgt_marker.core.claim import Claim
from cgt_marker.core.marker import Marker


@dataclass
class JsonlStore:
    """Append/replay JSONL store for reproducible claim and marker logs.

    This store is intentionally simple and is not a concurrent database.
    """

    path: str | Path
    _claims: list[Claim] = field(default_factory=list)
    _markers: dict[str, Marker] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.file_path.exists():
            self._load()

    def add_claim(self, claim: Claim) -> None:
        self._claims.append(claim)
        self._append("claim", claim.to_dict())

    def list_claims(self) -> list[Claim]:
        return list(self._claims)

    def add_marker(self, marker: Marker) -> None:
        self._markers[marker.id] = marker
        self._append("marker", marker.to_dict())

    def update_marker(self, marker: Marker) -> None:
        if marker.id not in self._markers:
            raise KeyError(f"Unknown marker id: {marker.id}")
        self._markers[marker.id] = marker
        self._append("marker", marker.to_dict())

    def list_markers(self) -> list[Marker]:
        return list(self._markers.values())

    def clear(self) -> None:
        self._claims.clear()
        self._markers.clear()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text("", encoding="utf-8")

    def _append(self, record_type: str, data: dict[str, Any]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"type": record_type, "data": data}, sort_keys=True) + "\n")

    def _load(self) -> None:
        for line in self.file_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record["type"] == "claim":
                self._claims.append(Claim.from_dict(record["data"]))
            elif record["type"] == "marker":
                marker = Marker.from_dict(record["data"])
                self._markers[marker.id] = marker

    @property
    def file_path(self) -> Path:
        return Path(self.path)

    @classmethod
    def save_state(
        cls,
        path: str | Path,
        *,
        claims: list[Claim],
        markers: list[Marker],
    ) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for claim in claims:
                record = {"type": "claim", "data": claim.to_dict()}
                handle.write(json.dumps(record, sort_keys=True) + "\n")
            for marker in markers:
                record = {"type": "marker", "data": marker.to_dict()}
                handle.write(json.dumps(record, sort_keys=True) + "\n")
