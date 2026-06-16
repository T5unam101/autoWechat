from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Sequence

from autowechat.config import load_config
from autowechat.engine import AutoReplyEngine
from autowechat.events import IncomingMessage
from autowechat.model import DeepSeekDecisionClient
from autowechat.sender import DryRunSender, SendMessage
from autowechat.wechat_sender import AppleScriptWeChatSender


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="autowechat")
    parser.add_argument("--config", required=True, help="Path to YAML config.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="Simulate one incoming message.")
    simulate_contact = simulate.add_mutually_exclusive_group(required=True)
    simulate_contact.add_argument("--remark-name", dest="contact")
    simulate_contact.add_argument("--contact", dest="contact", help="Alias for --remark-name.")
    simulate.add_argument("--message", required=True)
    simulate.add_argument("--advance-minutes", type=int, default=30)
    simulate.add_argument("--use-model", action="store_true")

    reply_once = subparsers.add_parser(
        "wechat-reply-once",
        help="Generate one guarded reply and optionally send it through macOS WeChat.",
    )
    reply_contact = reply_once.add_mutually_exclusive_group(required=True)
    reply_contact.add_argument("--remark-name", dest="contact")
    reply_contact.add_argument("--contact", dest="contact", help="Alias for --remark-name.")
    reply_once.add_argument("--message", required=True)
    reply_once.add_argument("--advance-minutes", type=int, default=30)
    reply_once.add_argument("--use-model", action="store_true")
    reply_once.add_argument("--real-send", action="store_true")

    send_test = subparsers.add_parser(
        "wechat-send-test",
        help="Send an explicit disclosure-bearing test message through macOS WeChat.",
    )
    send_contact = send_test.add_mutually_exclusive_group(required=True)
    send_contact.add_argument("--remark-name", dest="contact")
    send_contact.add_argument("--contact", dest="contact", help="Alias for --remark-name.")
    send_test.add_argument("--message", required=True)
    send_test.add_argument("--real-send", action="store_true")

    args = parser.parse_args(argv)
    config = load_config(args.config)

    if args.command == "simulate":
        now = datetime(2026, 6, 15, 12, 0)
        config, model_client = _configure_model(config, args.use_model)
        engine = AutoReplyEngine(config, DryRunSender(), model_client=model_client)
        engine.handle_incoming(
            IncomingMessage(
                contact=args.contact,
                text=args.message,
                timestamp=now,
            )
        )
        actions = engine.tick(now + timedelta(minutes=args.advance_minutes))
        for action in actions:
            print(json.dumps(asdict(action), ensure_ascii=False))
        return 0

    if args.command == "wechat-reply-once":
        if not args.real_send:
            print("Refusing to access WeChat without --real-send.")
            return 2
        now = datetime.now()
        config, model_client = _configure_model(config, args.use_model)
        sender = AppleScriptWeChatSender(
            app_name=config.wechat.app_name,
            delay_seconds=config.wechat.send_delay_seconds,
        )
        engine = AutoReplyEngine(config, sender, model_client=model_client)
        engine.handle_incoming(
            IncomingMessage(
                contact=args.contact,
                text=args.message,
                timestamp=now - timedelta(minutes=args.advance_minutes),
            )
        )
        for action in engine.tick(now):
            print(json.dumps(asdict(action), ensure_ascii=False))
        return 0

    if args.command == "wechat-send-test":
        if not args.real_send:
            print("Refusing to access WeChat without --real-send.")
            return 2
        sender = AppleScriptWeChatSender(
            app_name=config.wechat.app_name,
            delay_seconds=config.wechat.send_delay_seconds,
        )
        result = sender.send(SendMessage(contact=args.contact, text=args.message))
        print(json.dumps(asdict(result), ensure_ascii=False))
        return 0

    return 2


def _configure_model(config, use_model):
    if use_model and not config.model.enabled:
        config = replace(config, model=replace(config.model, enabled=True))
    model_client = DeepSeekDecisionClient(config.model) if config.model.enabled else None
    return config, model_client


if __name__ == "__main__":
    raise SystemExit(main())
