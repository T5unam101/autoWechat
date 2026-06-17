from __future__ import annotations

import json
import subprocess
from collections.abc import Callable

from autowechat.monitor import ObservedChat


Runner = Callable[[list[str], str, float], tuple[int, str, str]]


class AppleScriptWeChatMonitor:
    def __init__(
        self,
        app_name: str = "WeChat",
        delay_seconds: float = 0.3,
        runner: Runner | None = None,
    ):
        self.app_name = app_name
        self.delay_seconds = delay_seconds
        self.runner = runner or _run_osascript

    def poll(self, remark_names: list[str]) -> list[ObservedChat]:
        chats: list[ObservedChat] = []
        for remark_name in remark_names:
            try:
                code, stdout, _ = self.runner(
                    ["osascript"],
                    self._script(remark_name),
                    10,
                )
            except (TimeoutError, subprocess.TimeoutExpired):
                continue
            if code != 0:
                continue
            latest_text = _latest_meaningful_line(stdout)
            if latest_text:
                chats.append(ObservedChat(remark_name=remark_name, latest_text=latest_text))
        return chats

    def _script(self, remark_name: str) -> str:
        contact_literal = json.dumps(remark_name, ensure_ascii=False)
        app_literal = self.app_name.replace('"', '\\"')
        delay = f"{self.delay_seconds:.2f}"
        return f'''
set contactName to {contact_literal}
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
    set collectedText to ""
    try
      set collectedText to value of every static text of window 1 as text
    end try
    return collectedText
  end tell
end tell
'''


def _latest_meaningful_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if line not in {"聊天", "搜索", "WeChat", "微信"}:
            return line
    return ""


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
