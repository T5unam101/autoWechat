# autoWechat

Conservative local auto-reply assistant core for macOS WeChat.

This first version does not control the WeChat desktop UI yet. It implements the safe, testable core: configuration loading, whitelist checks, delayed pending state, manual-reply cancellation hooks, conservative reply classification, observation mode, dry-run send mode, and a simulation CLI.

## Safety Model

- Only whitelisted contacts are eligible.
- Group chats are out of scope for the first version.
- Every reply template must include `这是自动生成的回复`.
- Replies avoid direct address terms such as `你` and `您`.
- The core does not upload chat data or call online models.
- `mode: observe` records what would happen without sending.

## Setup

```bash
python -m pip install -e ".[dev]"
cp config.example.yaml config.yaml
```

Edit `config.yaml` with whitelist contacts and profile fields.

## Simulate A Message

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  simulate \
  --contact 张三 \
  --message "通知一下，周五会议改到下午三点" \
  --advance-minutes 30
```

Example output:

```json
{"status": "would_send", "contact": "张三", "reply": "这是自动生成的回复：已收到关于「周五会议」的消息，本人稍后看到后会亲自处理。", "reason": ""}
```

## Current Boundary

The package currently provides the local engine and CLI simulation. Real macOS WeChat Accessibility automation should be added behind `autowechat.sender.Sender` after observation-mode behavior is validated.

## Run Tests

```bash
PYTHONPATH=src pytest -v
```
