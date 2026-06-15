from autowechat.config import AppConfig, Limits, Profile, ReplyTemplates
from autowechat.reply import classify_message, render_reply


def make_config() -> AppConfig:
    return AppConfig(
        mode="observe",
        delay_minutes=30,
        whitelist={"张三"},
        profile=Profile(
            name="曲畅",
            location="上海",
            occupation="工程师",
            company_or_project="autoWechat",
            contact="example@example.com",
            available_time="工作日 10:00-18:00",
        ),
        limits=Limits(
            max_auto_replies_per_contact_per_day=3,
            min_gap_minutes_per_contact=120,
        ),
        templates=ReplyTemplates(
            profile_intro="这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。",
            receipt_with_summary="这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。",
            receipt_generic="这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。",
        ),
    )


def test_profile_question_renders_only_configured_profile_fields():
    decision = classify_message("方便说下所在地和联系方式吗")
    reply = render_reply(decision, make_config())

    assert decision.kind == "profile"
    assert "所在地：上海" in reply
    assert "联系方式：example@example.com" in reply
    assert reply.startswith("这是自动生成的回复")


def test_notice_message_uses_short_neutral_summary():
    decision = classify_message("通知一下，周五会议改到下午三点")
    reply = render_reply(decision, make_config())

    assert decision.kind == "receipt_with_summary"
    assert decision.summary == "周五会议"
    assert reply == "这是自动生成的回复：已收到关于「周五会议」的消息，本人稍后看到后会亲自处理。"


def test_uncertain_message_uses_generic_receipt():
    decision = classify_message("哈哈哈哈")
    reply = render_reply(decision, make_config())

    assert decision.kind == "receipt_generic"
    assert reply == "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"


def test_rendered_replies_avoid_direct_address_terms():
    for text in ["你在哪里", "通知一下，明天下午安排调整", "看到了吗"]:
        reply = render_reply(classify_message(text), make_config())
        assert "你" not in reply
        assert "您" not in reply
