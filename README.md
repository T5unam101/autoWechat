# autoWechat

Conservative local auto-reply assistant core for macOS WeChat.

This version implements the safe, testable core plus a guarded macOS WeChat sender for whitelist testing. It can classify messages locally or through DeepSeek, render deterministic disclosure-bearing replies, and send one generated reply to a named WeChat contact when explicitly requested.

## Safety Model

- Only whitelisted WeChat remark names are eligible.
- Group chats are out of scope for the first version.
- Every reply template must include `这是自动生成的回复`.
- Replies avoid direct address terms such as `你` and `您`.
- The core does not upload chat data or call online models.
- `mode: observe` records what would happen without sending.
- DeepSeek, when enabled, only returns a message type and short summary. It never writes final reply text.
- Real WeChat access requires an explicit `--real-send` flag.

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

## macOS WeChat Test Sending

Before real sending:

1. Open WeChat desktop for macOS and sign in.
2. Set a unique WeChat remark name for the test account, such as `autoWechat测试号`.
3. Add that exact remark name to `whitelist` in `config.yaml`.
4. Grant Terminal, iTerm, or the app running Python macOS Accessibility permission:
   `System Settings -> Privacy & Security -> Accessibility`.
5. Keep the WeChat app unlocked and visible during tests.

Send one generated auto-reply to a whitelisted contact:

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  wechat-reply-once \
  --remark-name autoWechat测试号 \
  --message "通知一下，周五会议改到下午三点" \
  --advance-minutes 30 \
  --use-model \
  --real-send
```

This command creates the same engine event as a 30-minute-old incoming message, generates the guarded reply, then uses AppleScript to activate WeChat, search the contact, paste the reply, and press Return.

Send an explicit disclosure-bearing test message:

```bash
PYTHONPATH=src python -m autowechat.cli \
  --config config.yaml \
  wechat-send-test \
  --remark-name autoWechat测试号 \
  --message "这是自动生成的回复：消息已收到，本人稍后看到后会亲自回复。" \
  --real-send
```

## Current Boundary

The current WeChat integration is a guarded one-shot sender. It does not yet continuously read incoming WeChat messages or detect manual replies from the live WeChat UI. Continuous monitoring should be added as a separate Accessibility adapter after one-shot sending is validated with a whitelist test account.

## Run Tests

```bash
PYTHONPATH=src pytest -v
```
