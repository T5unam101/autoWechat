from pathlib import Path

import pytest

from autowechat.config import AppConfig, ConfigError, load_config


def test_load_config_reads_required_fields(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text(
        """
mode: observe
delay_minutes: 30
whitelist:
  - 张三
profile:
  name: 曲畅
  location: 上海
  occupation: 工程师
  company_or_project: autoWechat
  contact: example@example.com
  available_time: 工作日 10:00-18:00
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

    config = load_config(path)

    assert isinstance(config, AppConfig)
    assert config.mode == "observe"
    assert config.delay_minutes == 30
    assert config.whitelist == {"张三"}
    assert config.profile.location == "上海"
    assert config.limits.max_auto_replies_per_contact_per_day == 3


def test_load_config_rejects_send_mode_without_disclosure(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text(
        """
mode: send
delay_minutes: 30
whitelist: [张三]
profile: {}
limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120
templates:
  profile_intro: "相关信息如下：{profile_summary}"
  receipt_with_summary: "已收到关于「{summary}」的消息"
  receipt_generic: "消息已收到"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="自动生成"):
        load_config(path)


def test_load_config_reads_model_and_wechat_sections(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text(
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
  enabled: true
  provider: deepseek
  api_key_env: DEEPSEEK_API_KEY
  base_url: "https://api.deepseek.com"
  model: deepseek-v4-flash
  thinking: disabled
  timeout_seconds: 8
wechat:
  app_name: WeChat
  send_delay_seconds: 0.3
""",
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.model.enabled is True
    assert config.model.provider == "deepseek"
    assert config.model.model == "deepseek-v4-flash"
    assert config.model.thinking == "disabled"
    assert config.wechat.app_name == "WeChat"


def test_load_config_defaults_model_to_disabled(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text(
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
""",
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.model.enabled is False
    assert config.model.api_key_env == "DEEPSEEK_API_KEY"


def test_load_config_allows_fractional_delay_minutes_for_testing(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text(
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

    config = load_config(path)

    assert config.delay_minutes == 0.01
