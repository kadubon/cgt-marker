from __future__ import annotations

from collections.abc import Sequence

from cgt_marker.core.marker import Marker, MarkerStatus
from cgt_marker.renderers.markdown import MarkdownRenderer


class PromptContextRenderer:
    """Render marker state for inclusion in prompts or agent context."""

    def __init__(self, *, include_non_open: bool = False) -> None:
        self.include_non_open = include_non_open
        self.markdown = MarkdownRenderer()

    def render(self, markers: Sequence[Marker]) -> str:
        selected = [
            marker
            for marker in markers
            if self.include_non_open or marker.status is MarkerStatus.OPEN
        ]
        return self.markdown.render(selected)
