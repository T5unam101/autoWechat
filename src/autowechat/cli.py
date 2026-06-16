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
from autowechat.sender import DryRunSender


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="autowechat")
    parser.add_argument("--config", required=True, help="Path to YAML config.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="Simulate one incoming message.")
    simulate.add_argument("--contact", required=True)
    simulate.add_argument("--message", required=True)
    simulate.add_argument("--advance-minutes", type=int, default=30)
    simulate.add_argument("--use-model", action="store_true")

    args = parser.parse_args(argv)
    config = load_config(args.config)

    if args.command == "simulate":
        now = datetime(2026, 6, 15, 12, 0)
        if args.use_model and not config.model.enabled:
            config = replace(config, model=replace(config.model, enabled=True))
        model_client = DeepSeekDecisionClient(config.model) if config.model.enabled else None
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

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
