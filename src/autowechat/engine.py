from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from autowechat.config import AppConfig, DISCLOSURE
from autowechat.events import IncomingMessage, ManualReply
from autowechat.reply import classify_message, render_reply
from autowechat.sender import SendMessage, Sender
from autowechat.state import AutoReplyState


@dataclass(frozen=True)
class EngineAction:
    status: str
    contact: str
    reply: str
    reason: str = ""


class AutoReplyEngine:
    def __init__(self, config: AppConfig, sender: Sender):
        self.config = config
        self.sender = sender
        self.state = AutoReplyState(
            delay_minutes=config.delay_minutes,
            whitelist=config.whitelist,
            limits=config.limits,
        )

    def handle_incoming(self, event: IncomingMessage) -> None:
        self.state.record_incoming(event)

    def handle_manual_reply(self, event: ManualReply) -> None:
        self.state.record_manual_reply(event)

    def tick(self, now: datetime) -> list[EngineAction]:
        actions: list[EngineAction] = []
        for contact in self.state.ready_contacts(now):
            pending = self.state.pending_for(contact)
            if pending is None:
                continue
            reply = render_reply(classify_message(pending.text), self.config)
            if DISCLOSURE not in reply:
                self.state.mark_skipped(contact)
                actions.append(EngineAction("skipped", contact, "", "missing_disclosure"))
                continue
            if self.config.mode == "observe":
                self.state.mark_sent(contact, now)
                actions.append(EngineAction("would_send", contact, reply))
                continue

            result = self.sender.send(SendMessage(contact=contact, text=reply))
            if result.ok:
                self.state.mark_sent(contact, now)
                actions.append(EngineAction("sent", contact, reply))
            else:
                self.state.mark_skipped(contact)
                actions.append(EngineAction("skipped", contact, reply, result.reason))
        return actions
