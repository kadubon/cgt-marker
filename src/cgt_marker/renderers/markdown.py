from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from cgt_marker.core.marker import Marker


class Renderer(Protocol):
    """Protocol for marker-to-text projections."""

    def render(self, markers: Sequence[Marker]) -> str: ...


class MarkdownRenderer:
    """Render markers as compact Markdown text."""

    title: str = "Open contradiction markers"

    def render(self, markers: Sequence[Marker]) -> str:
        visible = list(markers)
        if not visible:
            return f"{self.title}: none"

        lines = [f"{self.title}:"]
        for marker in visible:
            sources = self._sources(marker)
            lines.append(f"- {marker.id} [{marker.kind.value}] {marker.message}")
            if sources:
                lines.append(f"  sources: {', '.join(sources)}")
            lines.append(f"  status: {marker.status.value}")
        return "\n".join(lines)

    @staticmethod
    def _sources(marker: Marker) -> list[str]:
        sources: list[str] = []
        for evidence in marker.evidence:
            if evidence.source not in sources:
                sources.append(evidence.source)
        return sources
