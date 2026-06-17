from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ObservedChat:
    remark_name: str
    latest_text: str
    from_self: bool = False
    is_group: bool = False


class ChatMonitor(Protocol):
    def poll(self, remark_names: list[str]) -> list[ObservedChat]:
        ...
