from pathlib import Path

from autowechat.cli import main


def test_cli_simulate_outputs_would_send(tmp_path: Path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
mode: observe
delay_minutes: 30
whitelist: [张三]
profile:
  location: 上海
limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120
templates:
  profile_intro: "这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。"
  receipt_with_summary: "这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。"
  receipt_generic: "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"
""",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--config",
            str(config),
            "simulate",
            "--contact",
            "张三",
            "--message",
            "通知一下，周五会议改到下午三点",
            "--advance-minutes",
            "30",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "would_send" in output
    assert "周五会议" in output


def test_cli_simulate_can_force_model_flag(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    config = tmp_path / "config.yaml"
    config.write_text(
        """
mode: observe
delay_minutes: 30
whitelist: [张三]
profile: {}
limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120
templates:
  profile_intro: "这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。"
  receipt_with_summary: "这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。"
  receipt_generic: "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"
model:
  enabled: false
""",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--config",
            str(config),
            "simulate",
            "--contact",
            "张三",
            "--message",
            "通知一下，周五会议改到下午三点",
            "--advance-minutes",
            "30",
            "--use-model",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "would_send" in output


def test_cli_wechat_reply_once_requires_real_send_flag(tmp_path: Path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
mode: send
delay_minutes: 30
whitelist: [张三]
profile: {}
limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120
templates:
  profile_intro: "这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。"
  receipt_with_summary: "这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。"
  receipt_generic: "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"
""",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--config",
            str(config),
            "wechat-reply-once",
            "--contact",
            "张三",
            "--message",
            "通知一下，周五会议改到下午三点",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "--real-send" in output


def test_cli_wechat_reply_once_accepts_remark_name_alias(tmp_path: Path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
mode: send
delay_minutes: 30
whitelist: [autoWechat测试号]
profile: {}
limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120
templates:
  profile_intro: "这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。"
  receipt_with_summary: "这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。"
  receipt_generic: "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"
""",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--config",
            str(config),
            "wechat-reply-once",
            "--remark-name",
            "autoWechat测试号",
            "--message",
            "通知一下，周五会议改到下午三点",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "--real-send" in output


def test_cli_simulate_accepts_fractional_advance_minutes(tmp_path: Path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
mode: observe
delay_minutes: 0.01
whitelist: [小号]
profile: {}
limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120
templates:
  profile_intro: "这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。"
  receipt_with_summary: "这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。"
  receipt_generic: "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"
""",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--config",
            str(config),
            "simulate",
            "--remark-name",
            "小号",
            "--message",
            "通知一下，周五会议改到下午三点",
            "--advance-minutes",
            "0.01",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "would_send" in output


def test_cli_watch_requires_once_or_real_send_for_noninteractive_safety(tmp_path: Path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
mode: observe
delay_minutes: 0.01
whitelist: [小号]
profile: {}
limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120
templates:
  profile_intro: "这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。"
  receipt_with_summary: "这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。"
  receipt_generic: "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"
""",
        encoding="utf-8",
    )

    exit_code = main(["--config", str(config), "watch", "--interval-seconds", "0.1"])

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "--once" in output
