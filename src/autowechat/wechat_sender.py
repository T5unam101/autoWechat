from __future__ import annotations

import json
import subprocess
from collections.abc import Callable

from autowechat.config import DISCLOSURE
from autowechat.sender import SendMessage, SendResult


Runner = Callable[[list[str], str, float], tuple[int, str, str]]


class AppleScriptWeChatSender:
    def __init__(
        self,
        app_name: str = "WeChat",
        delay_seconds: float = 0.3,
        runner: Runner | None = None,
    ):
        self.app_name = app_name
        self.delay_seconds = delay_seconds
        self.runner = runner or _run_osascript

    def send(self, message: SendMessage) -> SendResult:
        if DISCLOSURE not in message.text:
            return SendResult(ok=False, reason="missing_disclosure")
        return SendResult(ok=False, reason="real_send_disabled")

    def _script(self, contact: str, text: str) -> str:
        contact_literal = json.dumps(contact, ensure_ascii=False)
        text_literal = json.dumps(text, ensure_ascii=False)
        app_literal = self.app_name.replace('"', '\\"')
        delay = f"{self.delay_seconds:.2f}"
        return f'''
set contactName to {contact_literal}
set replyText to {text_literal}
set the clipboard to replyText
tell application "{app_literal}" to activate
delay {delay}
tell application "System Events"
  tell process "{app_literal}"
    keystroke "f" using command down
    delay {delay}
    keystroke contactName
    delay {delay}
    key code 36
    delay {delay}
    keystroke "v" using command down
    delay {delay}
    key code 36
  end tell
end tell
'''


def _run_osascript(args: list[str], input_text: str, timeout: float) -> tuple[int, str, str]:
    completed = subprocess.run(
        args,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr
