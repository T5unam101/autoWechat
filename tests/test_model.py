import json

import pytest

from autowechat.config import ModelConfig
from autowechat.model import DeepSeekDecisionClient, ModelDecisionError


class FakeTransport:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    def post_json(self, url, headers, payload, timeout):
        self.requests.append((url, headers, payload, timeout))
        return self.payload


def test_deepseek_client_requests_json_decision(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    transport = FakeTransport(
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"kind": "receipt_with_summary", "summary": "周五会议"},
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }
    )
    client = DeepSeekDecisionClient(ModelConfig(enabled=True), transport=transport)

    decision = client.classify("通知一下，周五会议改到下午三点")

    assert decision.kind == "receipt_with_summary"
    assert decision.summary == "周五会议"
    url, headers, payload, timeout = transport.requests[0]
    assert url == "https://api.deepseek.com/chat/completions"
    assert headers["Authorization"] == "Bearer secret"
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["response_format"] == {"type": "json_object"}
    assert timeout == 8.0


def test_deepseek_client_rejects_invalid_kind(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    transport = FakeTransport(
        {"choices": [{"message": {"content": '{"kind":"free_chat","summary":"x"}'}}]}
    )
    client = DeepSeekDecisionClient(ModelConfig(enabled=True), transport=transport)

    with pytest.raises(ModelDecisionError, match="invalid kind"):
        client.classify("随便聊聊")


def test_deepseek_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = DeepSeekDecisionClient(ModelConfig(enabled=True))

    with pytest.raises(ModelDecisionError, match="DEEPSEEK_API_KEY"):
        client.classify("通知一下")
