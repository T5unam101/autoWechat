from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from autowechat.config import Limits
from autowechat.events import IncomingMessage, ManualReply


@dataclass
class PendingMessage:
    contact: str
    text: str
    timestamp: datetime
    canceled: bool = False


class AutoReplyState:
    def __init__(self, delay_minutes: int, whitelist: set[str], limits: Limits):
        self.delay = timedelta(minutes=delay_minutes)
        self.whitelist = set(whitelist)
        self.limits = limits
        self._pending: dict[str, PendingMessage] = {}
        self._last_sent_at: dict[str, datetime] = {}
        self._daily_counts: dict[tuple[str, date], int] = defaultdict(int)

    def record_incoming(self, event: IncomingMessage) -> None:
        if event.contact not in self.whitelist:
            return
        self._pending[event.contact] = PendingMessage(
            contact=event.contact,
            text=event.text,
            timestamp=event.timestamp,
        )

    def record_manual_reply(self, event: ManualReply) -> None:
        pending = self._pending.get(event.contact)
        if pending and event.timestamp >= pending.timestamp:
            pending.canceled = True

    def ready_contacts(self, now: datetime) -> list[str]:
        ready: list[str] = []
        for contact, pending in self._pending.items():
            if pending.canceled:
                continue
            if now - pending.timestamp >= self.delay and self.can_send(contact, now):
                ready.append(contact)
        return ready

    def pending_for(self, contact: str) -> PendingMessage | None:
        return self._pending.get(contact)

    def can_send(self, contact: str, now: datetime) -> bool:
        sent_today = self._daily_counts[(contact, now.date())]
        if sent_today >= self.limits.max_auto_replies_per_contact_per_day:
            return False
        last_sent = self._last_sent_at.get(contact)
        if last_sent is None:
            return True
        gap = timedelta(minutes=self.limits.min_gap_minutes_per_contact)
        return now - last_sent >= gap

    def mark_sent(self, contact: str, now: datetime) -> None:
        self._last_sent_at[contact] = now
        self._daily_counts[(contact, now.date())] += 1
        self._pending.pop(contact, None)

    def mark_skipped(self, contact: str) -> None:
        self._pending.pop(contact, None)
