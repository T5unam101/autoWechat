from datetime import datetime

from autowechat.config import AppConfig, Limits, Profile, ReplyTemplates
from autowechat.engine import AutoReplyEngine
from autowechat.events import IncomingMessage, ManualReply
from autowechat.model import ModelDecisionError
from autowechat.reply import ReplyDecision
from autowechat.sender import DryRunSender


def make_config(mode: str = "observe") -> AppConfig:
    return AppConfig(
        mode=mode,
        delay_minutes=30,
        whitelist={"张三"},
        profile=Profile(
            name="曲畅",
            location="上海",
            occupation="",
            company_or_project="",
            contact="",
            available_time="",
        ),
        limits=Limits(3, 120),
        templates=ReplyTemplates(
            profile_intro="这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。",
            receipt_with_summary="这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。",
            receipt_generic="这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。",
        ),
    )


def test_observe_mode_records_would_send_without_sender_call():
    sender = DryRunSender()
    engine = AutoReplyEngine(make_config("observe"), sender)
    engine.handle_incoming(
        IncomingMessage(
            "张三",
            "通知一下，周五会议改到下午三点",
            datetime(2026, 6, 15, 12, 0),
        )
    )

    actions = engine.tick(datetime(2026, 6, 15, 12, 30))

    assert actions[0].status == "would_send"
    assert actions[0].contact == "张三"
    assert "周五会议" in actions[0].reply
    assert sender.sent_messages == []


def test_send_mode_calls_sender_after_delay():
    sender = DryRunSender()
    engine = AutoReplyEngine(make_config("send"), sender)
    engine.handle_incoming(
        IncomingMessage("张三", "联系方式是什么", datetime(2026, 6, 15, 12, 0))
    )

    actions = engine.tick(datetime(2026, 6, 15, 12, 31))

    assert actions[0].status == "sent"
    assert sender.sent_messages[0].contact == "张三"
    assert sender.sent_messages[0].text.startswith("这是自动生成的回复")


def test_manual_reply_prevents_engine_action():
    sender = DryRunSender()
    engine = AutoReplyEngine(make_config("send"), sender)
    engine.handle_incoming(
        IncomingMessage("张三", "通知一下，周五会议", datetime(2026, 6, 15, 12, 0))
    )
    engine.handle_manual_reply(ManualReply("张三", datetime(2026, 6, 15, 12, 5)))

    assert engine.tick(datetime(2026, 6, 15, 12, 35)) == []
    assert sender.sent_messages == []


class FakeModelClient:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def classify(self, text):
        self.calls.append(text)
        if isinstance(self.decision, Exception):
            raise self.decision
        return self.decision


def test_enabled_model_decision_overrides_local_summary():
    config = make_config("observe")
    config = AppConfig(
        mode=config.mode,
        delay_minutes=config.delay_minutes,
        whitelist=config.whitelist,
        profile=config.profile,
        limits=config.limits,
        templates=config.templates,
        model=config.model.__class__(enabled=True),
        wechat=config.wechat,
    )
    model = FakeModelClient(ReplyDecision("receipt_with_summary", "项目资料"))
    engine = AutoReplyEngine(config, DryRunSender(), model_client=model)
    engine.handle_incoming(
        IncomingMessage("张三", "发你一个文件", datetime(2026, 6, 15, 12, 0))
    )

    actions = engine.tick(datetime(2026, 6, 15, 12, 30))

    assert model.calls == ["发你一个文件"]
    assert "项目资料" in actions[0].reply


def test_model_failure_falls_back_to_local_rules():
    config = make_config("observe")
    config = AppConfig(
        mode=config.mode,
        delay_minutes=config.delay_minutes,
        whitelist=config.whitelist,
        profile=config.profile,
        limits=config.limits,
        templates=config.templates,
        model=config.model.__class__(enabled=True),
        wechat=config.wechat,
    )
    engine = AutoReplyEngine(
        config,
        DryRunSender(),
        model_client=FakeModelClient(ModelDecisionError("boom")),
    )
    engine.handle_incoming(
        IncomingMessage("张三", "通知一下，周五会议改到下午三点", datetime(2026, 6, 15, 12, 0))
    )

    actions = engine.tick(datetime(2026, 6, 15, 12, 30))

    assert "周五会议" in actions[0].reply
