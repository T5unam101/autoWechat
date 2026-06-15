from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DISCLOSURE = "这是自动生成的回复"


class ConfigError(ValueError):
    """Raised when the local configuration is unsafe or invalid."""


@dataclass(frozen=True)
class Profile:
    name: str = ""
    location: str = ""
    occupation: str = ""
    company_or_project: str = ""
    contact: str = ""
    available_time: str = ""


@dataclass(frozen=True)
class Limits:
    max_auto_replies_per_contact_per_day: int
    min_gap_minutes_per_contact: int


@dataclass(frozen=True)
class ReplyTemplates:
    profile_intro: str
    receipt_with_summary: str
    receipt_generic: str


@dataclass(frozen=True)
class AppConfig:
    mode: str
    delay_minutes: int
    whitelist: set[str]
    profile: Profile
    limits: Limits
    templates: ReplyTemplates


def load_config(path: str | Path) -> AppConfig:
    data = _read_yaml(Path(path))

    mode = str(data.get("mode", "observe"))
    if mode not in {"observe", "send"}:
        raise ConfigError("mode must be 'observe' or 'send'")

    templates = _load_templates(_mapping(data.get("templates"), "templates"))
    _validate_templates(templates)

    return AppConfig(
        mode=mode,
        delay_minutes=_positive_int(data.get("delay_minutes", 30), "delay_minutes"),
        whitelist=set(str(name) for name in data.get("whitelist", [])),
        profile=_load_profile(_mapping(data.get("profile", {}), "profile")),
        limits=_load_limits(_mapping(data.get("limits"), "limits")),
        templates=templates,
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ConfigError(f"cannot read config: {path}") from exc
    if not isinstance(loaded, dict):
        raise ConfigError("config root must be a mapping")
    return loaded


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be a mapping")
    return value


def _load_profile(data: dict[str, Any]) -> Profile:
    return Profile(
        name=str(data.get("name", "")),
        location=str(data.get("location", "")),
        occupation=str(data.get("occupation", "")),
        company_or_project=str(data.get("company_or_project", "")),
        contact=str(data.get("contact", "")),
        available_time=str(data.get("available_time", "")),
    )


def _load_limits(data: dict[str, Any]) -> Limits:
    return Limits(
        max_auto_replies_per_contact_per_day=_positive_int(
            data.get("max_auto_replies_per_contact_per_day", 3),
            "limits.max_auto_replies_per_contact_per_day",
        ),
        min_gap_minutes_per_contact=_positive_int(
            data.get("min_gap_minutes_per_contact", 120),
            "limits.min_gap_minutes_per_contact",
        ),
    )


def _load_templates(data: dict[str, Any]) -> ReplyTemplates:
    try:
        return ReplyTemplates(
            profile_intro=str(data["profile_intro"]),
            receipt_with_summary=str(data["receipt_with_summary"]),
            receipt_generic=str(data["receipt_generic"]),
        )
    except KeyError as exc:
        raise ConfigError(f"missing template: {exc.args[0]}") from exc


def _validate_templates(templates: ReplyTemplates) -> None:
    for value in (
        templates.profile_intro,
        templates.receipt_with_summary,
        templates.receipt_generic,
    ):
        if DISCLOSURE not in value:
            raise ConfigError(f"template must include {DISCLOSURE}")


def _positive_int(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be a positive integer") from exc
    if parsed <= 0:
        raise ConfigError(f"{name} must be a positive integer")
    return parsed
