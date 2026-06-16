from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

from autowechat.config import ModelConfig
from autowechat.reply import ReplyDecision


ALLOWED_KINDS = {"profile", "receipt_with_summary", "receipt_generic"}


class ModelDecisionError(RuntimeError):
    """Raised when a model decision cannot be used safely."""


class JsonTransport(Protocol):
    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        ...


class UrlLibJsonTransport:
    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ModelDecisionError(f"model request failed: {exc}") from exc


class DeepSeekDecisionClient:
    def __init__(
        self,
        config: ModelConfig,
        transport: JsonTransport | None = None,
    ):
        self.config = config
        self.transport = transport or UrlLibJsonTransport()

    def classify(self, text: str) -> ReplyDecision:
        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise ModelDecisionError(f"missing API key env var: {self.config.api_key_env}")

        response = self.transport.post_json(
            f"{self.config.base_url}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            payload=self._payload(text),
            timeout=self.config.timeout_seconds,
        )
        return _parse_decision(_message_content(response))

    def _payload(self, text: str) -> dict[str, Any]:
        return {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "只对微信消息做安全分类。只输出 JSON，不要解释。"
                        "kind 只能是 profile、receipt_with_summary、receipt_generic。"
                        "summary 必须是 2 到 12 个中文字符的中性短主题；无法确定则为空字符串。"
                        "不要生成最终回复文本。"
                    ),
                },
                {"role": "user", "content": text},
            ],
            "thinking": {"type": self.config.thinking},
            "response_format": {"type": "json_object"},
            "stream": False,
        }


def _message_content(response: dict[str, Any]) -> str:
    try:
        return str(response["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelDecisionError("missing message content") from exc


def _parse_decision(content: str) -> ReplyDecision:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelDecisionError("model did not return JSON") from exc
    kind = str(data.get("kind", ""))
    if kind not in ALLOWED_KINDS:
        raise ModelDecisionError(f"invalid kind: {kind}")
    summary = str(data.get("summary", "")).strip() or None
    if kind != "receipt_with_summary":
        summary = None
    if summary and len(summary) > 12:
        raise ModelDecisionError("summary too long")
    return ReplyDecision(kind=kind, summary=summary)
