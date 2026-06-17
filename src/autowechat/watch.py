from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from autowechat.config import AppConfig
from autowechat.engine import AutoReplyEngine, EngineAction
from autowechat.events import IncomingMessage, ManualReply
from autowechat.monitor import ChatMonitor
from autowechat.sender import Sender


class WatchRunner:
    def __init__(self, config: AppConfig, monitor: ChatMonitor, sender: Sender, model_client=None):
        self.config = config
        self.monitor = monitor
        self.engine = AutoReplyEngine(config, sender, model_client=model_client)
        self._last_seen: dict[str, str] = {}

    def run_once(self, now: datetime | None = None) -> list[EngineAction]:
        current_time = now or datetime.now()
        for chat in self.monitor.poll(sorted(self.config.whitelist)):
            if chat.is_group:
                continue
            if chat.remark_name not in self.config.whitelist:
                continue
            previous = self._last_seen.get(chat.remark_name)
            if previous == chat.latest_text:
                continue
            self._last_seen[chat.remark_name] = chat.latest_text
            if chat.from_self:
                self.engine.handle_manual_reply(ManualReply(chat.remark_name, current_time))
            elif chat.latest_text.strip():
                self.engine.handle_incoming(
                    IncomingMessage(chat.remark_name, chat.latest_text, current_time)
                )
        return self.engine.tick(current_time)

    def run_forever(
        self,
        interval_seconds: float,
        emit: Callable[[EngineAction], None],
    ) -> None:
        while True:
            for action in self.run_once():
                emit(action)
            time.sleep(interval_seconds)
