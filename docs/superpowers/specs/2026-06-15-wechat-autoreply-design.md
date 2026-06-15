# macOS WeChat Auto Reply Design

## Goal

Build a conservative local assistant for the macOS WeChat desktop app. The assistant sends clearly labeled automatic replies only for whitelisted one-to-one chats when the user has not manually replied within 30 minutes.

The tool is not intended to imitate the user, hold conversations, or make commitments. It only answers simple profile-card questions and acknowledges received messages.

## Scope

In scope:

- macOS WeChat desktop app.
- Whitelisted one-to-one contacts only.
- Direct automatic sending after the delay expires.
- Every automatic message explicitly states that it is automatically generated.
- Fixed profile-card answers.
- Neutral receipt confirmation for notifications, arrangements, and transferred information.
- Local-only configuration, state, and logs.
- Observation mode before enabling real sending.

Out of scope for the first version:

- Group chat replies.
- Replies to non-whitelisted contacts.
- Human-like conversation.
- Client injection, reverse engineering, or WeChat protocol automation.
- Cloud syncing.
- Online model calls by default.
- Commitments such as accepting invitations, confirming attendance, approving requests, or promising immediate action.

## Core Behavior

The assistant starts in a default-silent state. It only reacts to messages from contacts listed in the whitelist.

When a whitelisted contact sends a message:

1. Record the latest visible incoming message and timestamp.
2. Start or refresh a 30-minute pending timer for that contact.
3. Watch for a manual reply from the user in the same chat.
4. If a manual reply is detected before the timer expires, cancel the pending automatic reply.
5. If no manual reply is detected after 30 minutes, prepare an automatic reply.
6. Before sending, confirm that the current target chat still matches the intended contact.
7. Send one automatic reply for that pending message round.

The assistant should avoid repeated replies. Each contact has per-day and minimum-gap limits.

## Reply Types

### Profile-Card Question

Use this when the message asks for configured personal information, such as name, location, occupation, company or project, contact method, or available time.

Template:

```text
这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。
```

The response may include only fields present in the local profile configuration.

### Receipt With Summary

Use this when the message appears to communicate a notice, arrangement, schedule, reminder, or transferred information.

Template:

```text
这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。
```

The summary must be short and neutral, such as `周五会议`, `明天下午安排`, or `项目资料`. If the assistant cannot produce a reliable summary, it must use the generic receipt template instead.

### Generic Receipt

Use this for uncertain, complex, or unsupported messages.

Template:

```text
这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。
```

## Language Rules

Automatic replies must:

- Include `这是自动生成的回复`.
- Avoid pretending to be a real-time human response.
- Avoid using `你`, `您`, `对方`, or similar direct forms of address.
- Avoid commitments, approvals, decisions, or promises.
- Avoid answering questions outside the configured profile card.
- Prefer short, neutral wording.

## Architecture

### Configuration Module

Loads local YAML configuration:

- Reply delay.
- Whitelisted contacts.
- Profile-card facts.
- Limits.
- Reply templates.
- Observation or send mode.

Example:

```yaml
mode: observe
delay_minutes: 30

whitelist:
  - 张三
  - 李四

profile:
  name: "曲畅"
  location: "上海"
  occupation: ""
  company_or_project: ""
  contact: ""
  available_time: ""

limits:
  max_auto_replies_per_contact_per_day: 3
  min_gap_minutes_per_contact: 120

templates:
  profile_intro: "这是自动生成的回复：相关信息如下：{profile_summary}。本人稍后看到后会亲自回复。"
  receipt_with_summary: "这是自动生成的回复：已收到关于「{summary}」的消息，本人稍后看到后会亲自处理。"
  receipt_generic: "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。"
```

### WeChat UI Monitor

Uses macOS Accessibility APIs to inspect and operate the visible WeChat desktop UI. The first version avoids WeChat client modification, private protocol automation, and reverse engineering.

Responsibilities:

- Detect current chat title.
- Identify visible incoming messages.
- Detect whether a chat is a group chat when possible.
- Detect whether the user has manually sent a message after the pending incoming message.
- Provide best-effort target verification before sending.

If UI inspection is unreliable, an optional OCR fallback may be added later using screen recording permission. OCR is not required for the first implementation plan unless Accessibility inspection is insufficient.

### State Machine

Tracks per-contact state:

- Latest pending incoming message timestamp.
- Latest pending message text or sanitized snippet.
- Detected summary.
- Timer deadline.
- Whether a manual reply has canceled the pending item.
- Last automatic reply time.
- Count of automatic replies for the current day.

States:

- `idle`: no pending message.
- `pending`: whitelisted incoming message observed and waiting for the delay.
- `canceled`: manual reply detected or target became invalid.
- `ready`: delay expired and reply is eligible.
- `sent`: automatic reply sent or logged in observation mode.
- `skipped`: limit, group chat, target mismatch, or other safety check prevented sending.

### Classifier And Summarizer

The first version uses conservative local rules.

Profile-card detection checks for keywords related to configured facts, such as location, occupation, company, project, contact, availability, and name.

Receipt detection checks for messages that look like notices or arrangements, including terms related to meetings, schedules, reminders, time, place, documents, or transfer of information.

Summary generation should produce a short phrase from visible keywords. When confidence is low, skip the summary and use the generic receipt.

### Sender

The sender focuses the intended WeChat chat, re-checks the chat title, fills the input field, and sends the message only if all safety checks pass.

Before sending, it must verify:

- The contact is in the whitelist.
- The chat is not a known group chat.
- The current chat title exactly matches the target contact.
- The delay has expired.
- No manual reply was detected.
- Per-contact limits allow sending.
- The message text includes the automatic-reply disclosure.

## Operating Modes

### Observation Mode

Observation mode performs all detection, timing, classification, and template rendering, but does not send messages. It logs what would have been sent.

This mode is required before real sending so the user can verify timing and classification behavior.

### Send Mode

Send mode enables direct automatic sending after all safety checks pass.

The user should begin with one or two trusted whitelist contacts before expanding the whitelist.

## Safety And Error Handling

The assistant must default to not sending.

Skip sending when:

- The contact is not whitelisted.
- The chat appears to be a group chat.
- The target chat cannot be verified.
- The current chat title does not exactly match the target.
- The assistant cannot determine whether the user already replied.
- Daily or minimum-gap limits are exceeded.
- WeChat is not available or UI automation fails.
- The generated reply does not include the automatic-reply disclosure.

If classification fails, use the generic receipt. If target verification fails, do not send.

## Logging And Privacy

Logs stay local. The first version does not upload chat content, profile data, or logs.

Default logs should avoid storing full message text. Store only event type, contact name, status, template, reason, and optional short summary.

Example:

```text
2026-06-15 14:31 张三 pending summary="周五会议"
2026-06-15 15:01 张三 auto_sent template=receipt_with_summary
2026-06-15 15:07 李四 skipped reason=manual_reply_detected
```

If a later version adds an online model for summarization, it must be a separate explicit setting and remain disabled by default.

## macOS Permissions

Expected permissions:

- Accessibility permission for reading and operating WeChat UI.
- Screen Recording permission only if OCR fallback is introduced.

The first version can run from Terminal. A later version may add a menu bar app or LaunchAgent for easier startup.

## Testing Plan

1. Unit-test configuration loading, template rendering, classification, summary fallback, limits, and state transitions.
2. Run simulation tests with fake contacts and messages without opening WeChat.
3. Run observation mode against real WeChat for one or two days.
4. Enable send mode for one or two trusted whitelisted contacts.
5. Expand the whitelist only after observing stable behavior.

## Success Criteria

- Non-whitelisted contacts never receive automatic replies.
- Group chats never receive automatic replies.
- Whitelisted contacts receive at most one reply per pending message round.
- Manual replies within the delay cancel automatic replies.
- Automatic replies are sent only after the configured delay.
- Every sent message clearly states that it is automatically generated.
- The assistant avoids direct address terms such as `你` and `您`.
- Uncertain messages fall back to a generic receipt instead of a risky answer.
