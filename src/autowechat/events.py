from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IncomingMessage:
    contact: str
    text: str
    timestamp: datetime


@dataclass(frozen=True)
class ManualReply:
    contact: str
    timestamp: datetime
