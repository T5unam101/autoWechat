from __future__ import annotations

from dataclasses import dataclass

from autowechat.config import AppConfig


@dataclass(frozen=True)
class ReplyDecision:
    kind: str
    summary: str | None = None


PROFILE_FIELDS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("name", "姓名", ("姓名", "名字", "怎么称呼", "叫啥", "叫什么")),
    ("location", "所在地", ("所在地", "在哪", "哪里", "城市", "地址")),
    ("occupation", "职业", ("职业", "工作", "做什么", "行业")),
    ("company_or_project", "公司/项目", ("公司", "项目", "团队")),
    ("contact", "联系方式", ("联系方式", "电话", "邮箱", "微信", "联系")),
    ("available_time", "可联系时间", ("什么时候有空", "可联系时间", "方便时间", "时间")),
)

NOTICE_KEYWORDS = (
    "通知",
    "会议",
    "安排",
    "提醒",
    "转达",
    "资料",
    "文件",
    "地点",
    "时间",
    "明天",
    "今天",
    "周一",
    "周二",
    "周三",
    "周四",
    "周五",
    "周六",
    "周日",
)


def classify_message(text: str) -> ReplyDecision:
    normalized = text.strip()
    if _is_profile_question(normalized):
        return ReplyDecision("profile")
    if any(keyword in normalized for keyword in NOTICE_KEYWORDS):
        summary = _extract_summary(normalized)
        if summary:
            return ReplyDecision("receipt_with_summary", summary)
    return ReplyDecision("receipt_generic")


def render_reply(decision: ReplyDecision, config: AppConfig) -> str:
    if decision.kind == "profile":
        return config.templates.profile_intro.format(
            profile_summary=_profile_summary(config),
        )
    if decision.kind == "receipt_with_summary" and decision.summary:
        return config.templates.receipt_with_summary.format(summary=decision.summary)
    return config.templates.receipt_generic


def _is_profile_question(text: str) -> bool:
    return any(keyword in text for _, _, keywords in PROFILE_FIELDS for keyword in keywords)


def _profile_summary(config: AppConfig) -> str:
    values: list[str] = []
    for attr, label, _ in PROFILE_FIELDS:
        value = getattr(config.profile, attr)
        if value:
            values.append(f"{label}：{value}")
    return "；".join(values) if values else "暂无可公开资料"


def _extract_summary(text: str) -> str | None:
    compact = text.replace("，", " ").replace(",", " ").replace("。", " ")
    parts = [part for part in compact.split() if part]
    for part in parts:
        if "会议" in part:
            prefix = _nearest_weekday(part)
            return f"{prefix}会议" if prefix else "会议"
    for part in parts:
        if "安排" in part:
            prefix = _nearest_time_word(part)
            return f"{prefix}安排" if prefix else "安排"
    for part in parts:
        if "资料" in part:
            return "项目资料" if "项目" in text else "资料"
    return None


def _nearest_weekday(text: str) -> str:
    for keyword in ("周一", "周二", "周三", "周四", "周五", "周六", "周日"):
        if keyword in text:
            return keyword
    return ""


def _nearest_time_word(text: str) -> str:
    for keyword in ("今天", "明天", "周一", "周二", "周三", "周四", "周五", "周六", "周日"):
        if keyword in text:
            return keyword
    return ""
