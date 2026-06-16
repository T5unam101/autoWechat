from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from autowechat.config import AppConfig, DISCLOSURE
from autowechat.events import IncomingMessage, ManualReply
from autowechat.model import ModelDecisionError
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
    def __init__(self, config: AppConfig, sender: Sender, model_client=None):
        self.config = config
        self.sender = sender
        self.model_client = model_client
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
            reply = render_reply(self._classify(pending.text), self.config)
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

    def _classify(self, text: str):
        if self.config.model.enabled and self.model_client is not None:
            try:
                return self.model_client.classify(text)
            except ModelDecisionError:
                pass
        return classify_message(text)
