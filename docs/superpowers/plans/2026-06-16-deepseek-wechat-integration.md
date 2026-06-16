# DeepSeek And WeChat Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DeepSeek-backed message classification and a guarded macOS WeChat sender for whitelist testing.

**Architecture:** Keep final reply text template-owned and deterministic. DeepSeek may only return a structured decision (`profile`, `receipt_with_summary`, or `receipt_generic`) and optional short summary. macOS WeChat integration is a sender behind the existing `Sender` protocol, using AppleScript UI automation for explicit test sends and one-shot generated replies.

**Tech Stack:** Python 3.11+, pytest, PyYAML, urllib, subprocess, AppleScript via `osascript`.

---

## Tasks

- [ ] Extend config with optional `model` and `wechat` sections.
- [ ] Add a DeepSeek client that calls `/chat/completions`, requests JSON output, parses only allowed fields, and falls back safely on failure.
- [ ] Let `AutoReplyEngine` use an injected model client only when `model.enabled` is true.
- [ ] Add an AppleScript-backed WeChat sender that can open a contact and paste/send a message.
- [ ] Add CLI commands for `simulate --use-model`, `wechat-send-test`, and `wechat-reply-once`.
- [ ] Update README with DeepSeek key setup, macOS Accessibility permissions, and whitelist testing flow.
- [ ] Run full tests and push the feature branch.

## Safety Rules

- Never store API keys in YAML; read `DEEPSEEK_API_KEY`.
- The model never writes final reply text.
- Any invalid model response falls back to local rules.
- WeChat sender refuses messages missing `这是自动生成的回复` unless using explicit `wechat-send-test`.
- Real send commands require an explicit `--real-send` flag.
- The first WeChat integration sends only to a named contact; continuous UI monitoring is a later adapter task.
