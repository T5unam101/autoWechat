from autowechat.wechat_monitor import AppleScriptWeChatMonitor


class FakeRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, args, input_text, timeout):
        self.calls.append((args, input_text, timeout))
        return 0, "聊天\n通知一下，周五会议改到下午三点\n", ""


def test_applescript_wechat_monitor_reads_latest_static_text_for_remark_name():
    runner = FakeRunner()
    monitor = AppleScriptWeChatMonitor(app_name="WeChat", delay_seconds=0.1, runner=runner)

    chats = monitor.poll(["小号"])

    assert chats[0].remark_name == "小号"
    assert chats[0].latest_text == "通知一下，周五会议改到下午三点"
    args, script, timeout = runner.calls[0]
    assert args == ["osascript"]
    assert 'set contactName to "小号"' in script
    assert 'tell application "WeChat" to activate' in script
    assert timeout == 10


def test_applescript_wechat_monitor_skips_when_runner_times_out():
    def timeout_runner(args, input_text, timeout):
        raise TimeoutError("osascript timed out")

    monitor = AppleScriptWeChatMonitor(runner=timeout_runner)

    assert monitor.poll(["小号"]) == []
