# Glance

**Minecraft Security Interceptor** — HTTPS MITM tool that protects you from malicious mods and catches attackers.

## Why?

Malicious mods and clients contain:

- **Stealers** — steal your Minecraft account, browser passwords, session tokens
- **RATs** — full remote control over your computer
- **Keyloggers** — log everything you type
- **Doxing tools** — collect your personal information

Attackers use Discord webhooks and Telegram bots to receive your stolen data.

## What it does

Glance intercepts HTTPS traffic from Minecraft, detects these requests, **blocks your data from reaching attackers**, and captures their webhook URLs and bot tokens for reporting.

## Installation

### From Source

1. Install [Python 3.8+](https://python.org)
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### From Releases

1. Download the appropriate build for your platform from [Releases](https://github.com/DedInc/glance/releases)
2. ⚠️ **Important:** Download and install [mitmproxy](https://www.mitmproxy.org/downloads/) — it is required but not included in the release builds
3. Run the executable directly

## Usage

```bash
python glance.py
```

That's it. Glance will find Java, install certificates, and launch Minecraft with protection.

Intercepted requests are saved to `./exports/`.

## Configuration

Edit `core/config.py` to customize:

- `STRICT_MODE` — `False` allows known Minecraft hosts, `True` blocks everything untrusted
- `SUSPICIOUS_URLS` — list of URL patterns to detect
- `PATTERNS` — regex patterns for tokens (Discord, Telegram, etc.)
- `IGNORE_HOSTS` — hosts that bypass interception

## Notes

- Run as Administrator (Windows) or with `sudo` (Linux/macOS) for certificate installation
- Works on Windows, Linux, macOS

## Report Attackers

When Glance catches an attacker's infrastructure in `./exports/`:

- **Discord Webhooks** — report to [Discord Trust & Safety](https://discord.com/safety)
- **Telegram Bots** — report via [@BotSupport](https://t.me/BotSupport)

Get their infrastructure banned. Your data never reached them — Glance blocked it.
