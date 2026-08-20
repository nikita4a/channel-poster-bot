# Channel Poster Bot

Telegram bot for publishing rich posts to channels with **premium emoji**, **inline keyboards**, and **format selection** (HTML / MarkdownV2 / Plain).

## Features

- **Premium emoji** — preserves `custom_emoji` entities from incoming messages
- **Inline keyboards** — `/keyboard Btn - url | Btn2 - url2`
- **Format selector** — HTML / MarkdownV2 / Plain (buttons in preview)
- **Channel management** — `/channel @username`
- **Preview before publish** — edit, change format, then publish
- **Zero dependencies** — only `httpx`, no aiogram/python-telegram-bot

## Quick Start

```bash
# 1. Clone
git clone https://github.com/reformboss/channel-poster-bot
cd channel-poster-bot

# 2. Set token
export BOT_TOKEN=your_token_from_BotFather
# or edit bot3.py and replace TOK variable

# 3. Install
pip install httpx

# 4. Run
python bot3.py
```

## Usage

1. Open `@your_bot` in Telegram
2. `/channel @your_channel` — set target channel (bot must be admin)
3. Send any text with emoji — bot shows preview
4. Choose format (HTML/Markdown/Plain) and click «Publish»

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome + menu |
| `/channel @name` | Set target channel |
| `/post text` | Create draft |
| `/keyboard Btn - url \| Btn2 - url2` | Add inline buttons |
| `/format html\|md\|plain` | Set parse mode |
| `/publish` | Publish immediately |

## How Premium Emoji Works

When user sends a message with premium emoji, Telegram Bot API includes `MessageEntityCustomEmoji` in the `entities` array. The bot preserves these entities and passes them to `sendMessage` — so premium emoji render correctly in the channel.

## License

MIT