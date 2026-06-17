from datetime import datetime, timedelta

from autowechat.config import AppConfig, Limits, Profile, ReplyTemplates
from autowechat.monitor import ObservedChat
from autowechat.sender import DryRunSender
from autowechat.watch import WatchRunner


class FakeMonitor:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)

    def poll(self, remark_names):
        return self.snapshots.pop(0) if self.snapshots else []


def make_config(mode: str = "observe") -> AppConfig:
    return AppConfig(
        mode=mode,
        delay_minutes=0.01,
        whitelist={"小号"},
        profile=Profile(),
        limits=Limits(3, 120),
        templates=ReplyTemplates(
            profile_intro="这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。",
            receipt_with_summary="这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。",
            receipt_generic="这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。",
        ),
    )


def test_watch_runner_emits_action_after_delay_for_new_observed_message():
    start = datetime(2026, 6, 17, 10, 0)
    monitor = FakeMonitor([[ObservedChat("小号", "通知一下，周五会议改到下午三点")]])
    runner = WatchRunner(make_config(), monitor, DryRunSender())

    assert runner.run_once(start) == []
    actions = runner.run_once(start + timedelta(minutes=0.01))

    assert actions[0].status == "would_send"
    assert actions[0].contact == "小号"
    assert "周五会议" in actions[0].reply


def test_watch_runner_does_not_reschedule_identical_latest_message():
    start = datetime(2026, 6, 17, 10, 0)
    monitor = FakeMonitor(
        [
            [ObservedChat("小号", "通知一下，周五会议改到下午三点")],
            [ObservedChat("小号", "通知一下，周五会议改到下午三点")],
        ]
    )
    runner = WatchRunner(make_config(), monitor, DryRunSender())

    runner.run_once(start)
    actions = runner.run_once(start + timedelta(minutes=0.005))

    assert actions == []
