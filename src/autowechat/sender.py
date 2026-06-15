from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SendMessage:
    contact: str
    text: str


@dataclass(frozen=True)
class SendResult:
    ok: bool
    reason: str = ""


class Sender(Protocol):
    def send(self, message: SendMessage) -> SendResult:
        ...


class DryRunSender:
    def __init__(self) -> None:
        self.sent_messages: list[SendMessage] = []

    def send(self, message: SendMessage) -> SendResult:
        self.sent_messages.append(message)
        return SendResult(ok=True)
