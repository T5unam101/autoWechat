from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any


class JsonlLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def log(self, event: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
