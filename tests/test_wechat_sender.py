from autowechat.sender import SendMessage
from autowechat.wechat_sender import AppleScriptWeChatSender


class FakeRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, args, input_text, timeout):
        self.calls.append((args, input_text, timeout))
        return 0, "", ""


def test_applescript_sender_rejects_reply_without_disclosure():
    runner = FakeRunner()
    sender = AppleScriptWeChatSender(runner=runner)

    result = sender.send(SendMessage(contact="张三", text="普通消息"))

    assert not result.ok
    assert result.reason == "missing_disclosure"
    assert runner.calls == []


def test_applescript_sender_refuses_safe_reply_without_typing():
    runner = FakeRunner()
    sender = AppleScriptWeChatSender(app_name="WeChat", delay_seconds=0.1, runner=runner)

    result = sender.send(
        SendMessage(
            contact="张三",
            text="这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。",
        )
    )

    assert not result.ok
    assert result.reason == "real_send_disabled"
    assert runner.calls == []
