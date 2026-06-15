from datetime import datetime, timedelta

from autowechat.config import Limits
from autowechat.events import IncomingMessage, ManualReply
from autowechat.state import AutoReplyState


def test_non_whitelisted_message_is_ignored():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(3, 120))
    event = IncomingMessage(
        contact="陌生人",
        text="在吗",
        timestamp=datetime(2026, 6, 15, 12, 0),
    )

    state.record_incoming(event)

    assert state.ready_contacts(datetime(2026, 6, 15, 12, 31)) == []


def test_pending_message_becomes_ready_after_delay():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(3, 120))
    event = IncomingMessage(
        contact="张三",
        text="通知一下，周五会议",
        timestamp=datetime(2026, 6, 15, 12, 0),
    )

    state.record_incoming(event)

    assert state.ready_contacts(datetime(2026, 6, 15, 12, 29)) == []
    assert state.ready_contacts(datetime(2026, 6, 15, 12, 30)) == ["张三"]


def test_manual_reply_cancels_pending_message():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(3, 120))
    state.record_incoming(
        IncomingMessage("张三", "通知一下，周五会议", datetime(2026, 6, 15, 12, 0))
    )

    state.record_manual_reply(ManualReply("张三", datetime(2026, 6, 15, 12, 10)))

    assert state.ready_contacts(datetime(2026, 6, 15, 12, 40)) == []


def test_daily_and_gap_limits_block_excess_replies():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(1, 120))
    first_time = datetime(2026, 6, 15, 12, 30)
    state.mark_sent("张三", first_time)

    assert not state.can_send("张三", first_time + timedelta(minutes=121))
