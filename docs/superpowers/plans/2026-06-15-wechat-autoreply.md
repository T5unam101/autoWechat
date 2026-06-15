# WeChat Auto Reply Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first-version local macOS WeChat auto-reply assistant with conservative profile replies, receipt confirmations, observation mode, and guarded send mode.

**Architecture:** The first version separates the testable reply engine from macOS UI automation. Core modules load YAML configuration, classify messages, render safe templates, track pending replies, enforce limits, and run a simulation/observation CLI. The WeChat sender is represented by a strict interface plus a dry-run implementation; real Accessibility automation can be added behind that interface after the core is proven.

**Tech Stack:** Python 3.11+, pytest, PyYAML, dataclasses, argparse, local JSONL logs.

---

## File Structure

- `pyproject.toml`: package metadata and pytest configuration.
- `README.md`: setup, configuration, observation mode, and safety notes.
- `config.example.yaml`: editable example configuration.
- `src/autowechat/__init__.py`: package marker and version.
- `src/autowechat/config.py`: YAML loading and config dataclasses.
- `src/autowechat/reply.py`: profile formatting, classification, summary extraction, template rendering, safety validation.
- `src/autowechat/state.py`: per-contact pending state, delay checks, manual-reply cancellation, limits.
- `src/autowechat/events.py`: event dataclasses shared by CLI and engine.
- `src/autowechat/engine.py`: orchestrates incoming/manual events, state machine, reply generation, and sending decisions.
- `src/autowechat/sender.py`: sender protocol plus dry-run sender.
- `src/autowechat/logging.py`: JSONL local event logger.
- `src/autowechat/cli.py`: simulation/observation CLI entrypoint.
- `tests/`: unit tests for config, reply, state, engine, and CLI smoke behavior.

## Task 1: Project Skeleton And Config Loading

**Files:**
- Create: `pyproject.toml`
- Create: `src/autowechat/__init__.py`
- Create: `src/autowechat/config.py`
- Create: `config.example.yaml`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_config.py -v`

Expected: FAIL because `autowechat.config` does not exist.

- [ ] **Step 3: Implement minimal config module**

Create dataclasses for profile, limits, templates, and app config. `load_config()` must parse YAML, default missing profile fields to empty strings, convert whitelist to a set, validate mode is `observe` or `send`, and require every template to include `这是自动生成的回复`.

- [ ] **Step 4: Add example config**

`config.example.yaml` should match the spec defaults and use `mode: observe`.

- [ ] **Step 5: Run tests**

Run: `PYTHONPATH=src pytest tests/test_config.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml config.example.yaml src/autowechat/__init__.py src/autowechat/config.py tests/test_config.py
git commit -m "feat: add config loading"
```

## Task 2: Reply Classification And Safe Rendering

**Files:**
- Create: `src/autowechat/reply.py`
- Test: `tests/test_reply.py`

- [ ] **Step 1: Write failing reply tests**

```python
from autowechat.config import Limits, Profile, ReplyTemplates, AppConfig
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
        limits=Limits(max_auto_replies_per_contact_per_day=3, min_gap_minutes_per_contact=120),
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_reply.py -v`

Expected: FAIL because `autowechat.reply` does not exist.

- [ ] **Step 3: Implement minimal reply module**

Add `ReplyDecision(kind: str, summary: str | None = None)`, `classify_message(text: str)`, `render_reply(decision, config)`, and helpers for profile summaries and notice summaries.

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=src pytest tests/test_reply.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/autowechat/reply.py tests/test_reply.py
git commit -m "feat: add safe reply rendering"
```

## Task 3: Pending State And Limits

**Files:**
- Create: `src/autowechat/events.py`
- Create: `src/autowechat/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Write failing state tests**

```python
from datetime import datetime, timedelta

from autowechat.config import Limits
from autowechat.events import IncomingMessage, ManualReply
from autowechat.state import AutoReplyState


def test_non_whitelisted_message_is_ignored():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(3, 120))
    event = IncomingMessage(contact="陌生人", text="在吗", timestamp=datetime(2026, 6, 15, 12, 0))

    state.record_incoming(event)

    assert state.ready_contacts(datetime(2026, 6, 15, 12, 31)) == []


def test_pending_message_becomes_ready_after_delay():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(3, 120))
    event = IncomingMessage(contact="张三", text="通知一下，周五会议", timestamp=datetime(2026, 6, 15, 12, 0))

    state.record_incoming(event)

    assert state.ready_contacts(datetime(2026, 6, 15, 12, 29)) == []
    assert state.ready_contacts(datetime(2026, 6, 15, 12, 30)) == ["张三"]


def test_manual_reply_cancels_pending_message():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(3, 120))
    state.record_incoming(IncomingMessage("张三", "通知一下，周五会议", datetime(2026, 6, 15, 12, 0)))

    state.record_manual_reply(ManualReply("张三", datetime(2026, 6, 15, 12, 10)))

    assert state.ready_contacts(datetime(2026, 6, 15, 12, 40)) == []


def test_daily_and_gap_limits_block_excess_replies():
    state = AutoReplyState(delay_minutes=30, whitelist={"张三"}, limits=Limits(1, 120))
    first_time = datetime(2026, 6, 15, 12, 30)
    state.mark_sent("张三", first_time)

    assert not state.can_send("张三", first_time + timedelta(minutes=121))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_state.py -v`

Expected: FAIL because `autowechat.state` does not exist.

- [ ] **Step 3: Implement state module**

Add incoming/manual event dataclasses and `AutoReplyState` with pending records, `ready_contacts(now)`, `pending_for(contact)`, `record_manual_reply()`, `can_send()`, `mark_sent()`, and `mark_skipped()`.

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=src pytest tests/test_state.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/autowechat/events.py src/autowechat/state.py tests/test_state.py
git commit -m "feat: add pending reply state"
```

## Task 4: Engine, Dry-Run Sender, And Local Logs

**Files:**
- Create: `src/autowechat/sender.py`
- Create: `src/autowechat/logging.py`
- Create: `src/autowechat/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write failing engine tests**

```python
from datetime import datetime

from autowechat.config import AppConfig, Limits, Profile, ReplyTemplates
from autowechat.engine import AutoReplyEngine
from autowechat.events import IncomingMessage, ManualReply
from autowechat.sender import DryRunSender


def make_config(mode: str = "observe") -> AppConfig:
    return AppConfig(
        mode=mode,
        delay_minutes=30,
        whitelist={"张三"},
        profile=Profile(name="曲畅", location="上海", occupation="", company_or_project="", contact="", available_time=""),
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
    engine.handle_incoming(IncomingMessage("张三", "通知一下，周五会议改到下午三点", datetime(2026, 6, 15, 12, 0)))

    actions = engine.tick(datetime(2026, 6, 15, 12, 30))

    assert actions[0].status == "would_send"
    assert actions[0].contact == "张三"
    assert "周五会议" in actions[0].reply
    assert sender.sent_messages == []


def test_send_mode_calls_sender_after_delay():
    sender = DryRunSender()
    engine = AutoReplyEngine(make_config("send"), sender)
    engine.handle_incoming(IncomingMessage("张三", "联系方式是什么", datetime(2026, 6, 15, 12, 0)))

    actions = engine.tick(datetime(2026, 6, 15, 12, 31))

    assert actions[0].status == "sent"
    assert sender.sent_messages[0].contact == "张三"
    assert sender.sent_messages[0].text.startswith("这是自动生成的回复")


def test_manual_reply_prevents_engine_action():
    sender = DryRunSender()
    engine = AutoReplyEngine(make_config("send"), sender)
    engine.handle_incoming(IncomingMessage("张三", "通知一下，周五会议", datetime(2026, 6, 15, 12, 0)))
    engine.handle_manual_reply(ManualReply("张三", datetime(2026, 6, 15, 12, 5)))

    assert engine.tick(datetime(2026, 6, 15, 12, 35)) == []
    assert sender.sent_messages == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_engine.py -v`

Expected: FAIL because `autowechat.engine` does not exist.

- [ ] **Step 3: Implement engine and dry-run sender**

Add `SendMessage`, `SendResult`, `DryRunSender`, `EngineAction`, and `AutoReplyEngine`. The engine must always render a disclosure-bearing reply and must call the sender only in `send` mode.

- [ ] **Step 4: Add JSONL event logger**

Add `JsonlLogger.log(action)` that appends event dictionaries without full incoming message text.

- [ ] **Step 5: Run tests**

Run: `PYTHONPATH=src pytest tests/test_engine.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/autowechat/sender.py src/autowechat/logging.py src/autowechat/engine.py tests/test_engine.py
git commit -m "feat: add auto reply engine"
```

## Task 5: CLI Simulation And Documentation

**Files:**
- Create: `src/autowechat/cli.py`
- Create: `README.md`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI smoke test**

```python
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

    exit_code = main([
        "--config",
        str(config),
        "simulate",
        "--contact",
        "张三",
        "--message",
        "通知一下，周五会议改到下午三点",
        "--advance-minutes",
        "30",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "would_send" in output
    assert "周五会议" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_cli.py -v`

Expected: FAIL because `autowechat.cli` does not exist.

- [ ] **Step 3: Implement CLI**

Add `simulate` subcommand that loads config, creates an engine, records one incoming message at a fixed current time, advances the clock by the requested minutes, and prints JSON actions.

- [ ] **Step 4: Write README**

Document install commands, config copy/edit flow, simulation command, observation-mode safety, and the fact that real macOS WeChat UI automation is not enabled in the first core implementation.

- [ ] **Step 5: Run tests**

Run: `PYTHONPATH=src pytest tests/test_cli.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/autowechat/cli.py README.md tests/test_cli.py
git commit -m "feat: add simulation CLI"
```

## Task 6: Full Verification And Push

**Files:**
- Modify: none unless verification finds an issue.

- [ ] **Step 1: Run full test suite**

Run: `PYTHONPATH=src pytest -v`

Expected: all tests PASS.

- [ ] **Step 2: Check git state**

Run: `git status --short --branch`

Expected: clean working tree on `feature/wechat-autoreply`.

- [ ] **Step 3: Push branch**

Run: `git push`

Expected: branch updates on `origin/feature/wechat-autoreply`.

## Self-Review Notes

- Spec coverage: configuration, disclosure templates, profile replies, receipt summaries, generic fallback, whitelist-only behavior, delay, manual cancellation, limits, local logs, observation mode, and send-mode boundaries are covered.
- Known first-version boundary: real macOS Accessibility control is intentionally deferred behind `sender.py`; the implemented first version is the safe core plus simulation/observation foundation.
- Placeholder scan: no implementation steps require unspecified behavior; each task includes concrete tests and commands.
