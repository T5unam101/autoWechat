# autoWechat

Conservative local auto-reply assistant core for macOS WeChat.

This version implements the safe, testable core plus macOS WeChat observation for whitelist testing. It can classify messages locally or through DeepSeek and render deterministic disclosure-bearing reply drafts. Real keyboard-driven WeChat sending is disabled for safety.

## Safety Model

- Only whitelisted WeChat remark names are eligible.
- Group chats are out of scope for the first version.
- Every reply template must include `这是自动生成的回复`.
- Replies avoid direct address terms such as `你` and `您`.
- The core does not upload chat data or call online models.
- The app records what would happen without sending.
- DeepSeek, when enabled, only returns a message type and short summary. It never writes final reply text.
- Real keyboard-driven WeChat sending is disabled because macOS focus changes can cause unintended typing.

## Setup

```bash
python -m pip install -e ".[dev]"
cp config.example.yaml config.yaml
```

Edit `config.yaml` with whitelist remark names and profile fields. The `whitelist` values should match the exact WeChat contact remark name you type into the desktop search box, for example `autoWechat测试号`.

## DeepSeek Setup

DeepSeek is optional. Local rules are used when `model.enabled` is `false`.

Set the API key in the shell instead of writing it into YAML:

```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key"
```

Enable DeepSeek in `config.yaml`:

```yaml
model:
  enabled: true
  provider: deepseek
  api_key_env: DEEPSEEK_API_KEY
  base_url: "https://api.deepseek.com"
  model: deepseek-v4-flash
  thinking: disabled
  timeout_seconds: 8
```

DeepSeek is used through its OpenAI-compatible chat completions API. The default model is `deepseek-v4-flash`; `thinking` is disabled because this app only needs short classification and summary output.

## Simulate A Message

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  simulate \
  --remark-name autoWechat测试号 \
  --message "通知一下，周五会议改到下午三点" \
  --advance-minutes 30
```

Example output:

```json
{"status": "would_send", "contact": "autoWechat测试号", "reply": "这是自动生成的回复：已收到关于「周五会议」的消息，本人稍后看到后会亲自处理。", "reason": ""}
```

Force DeepSeek for one simulation even if `model.enabled` is false:

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  simulate \
  --remark-name autoWechat测试号 \
  --message "通知一下，周五会议改到下午三点" \
  --advance-minutes 30 \
  --use-model
```

If DeepSeek fails or returns invalid JSON, the engine falls back to local rules.

## macOS WeChat Draft Testing

Before observing WeChat:

1. Open WeChat desktop for macOS and sign in.
2. Set a unique WeChat remark name for the test account, such as `autoWechat测试号`.
3. Add that exact remark name to `whitelist` in `config.yaml`.
4. Grant Terminal, iTerm, or the app running Python macOS Accessibility permission:
   `System Settings -> Privacy & Security -> Accessibility`.
5. Keep the WeChat app unlocked and visible during tests.

Generate one auto-reply draft for a whitelisted contact:

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  wechat-reply-once \
  --remark-name autoWechat测试号 \
  --message "通知一下，周五会议改到下午三点" \
  --advance-minutes 30 \
  --use-model
```

This command creates the same engine event as a 30-minute-old incoming message and prints the guarded reply draft. Copy the reply manually if you want to send it.

The old `--real-send` path is disabled for safety:

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  wechat-reply-once \
  --remark-name autoWechat测试号 \
  --message "通知一下，周五会议改到下午三点" \
  --real-send
```

This exits without touching WeChat.

## Continuous Watcher

The watcher polls whitelisted WeChat remark names through macOS UI automation. It is conservative: if the UI text cannot be read, it skips that contact.

Run one observation pass without sending:

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  watch \
  --once \
  --use-model
```

Continuous watch is intentionally dry-run only. It prints generated actions and drafts:

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  watch \
  --interval-seconds 5 \
  --once \
  --use-model
```

Important: `watch` searches each whitelisted remark name, reads visible static text from the WeChat window, and treats the latest readable line as the newest message. This is the first Accessibility-based listener and may need adjustment for your WeChat version. Keep `delay_minutes` short while testing with a whitelist test account, then move it back to `30`.

## Current Boundary

The current listener reads visible WeChat UI text through AppleScript. It does not use private WeChat APIs or local chat databases. Real automatic sending is disabled. Manual-reply detection depends on what the WeChat UI exposes; if the UI cannot distinguish message direction, the watcher behaves conservatively by only generating drafts after the configured delay and per-contact limits.

## Run Tests

```bash
PYTHONPATH=src pytest -v
```
