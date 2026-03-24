<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d0d0d,30:0a192f,60:112240,100:1a1a2e&height=220&section=header&text=Telegram%20OSINT%20Bot&fontSize=52&fontColor=00d9ff&animation=fadeIn&fontAlignY=40&desc=Intelligence%20%E2%80%A2%20Profiling%20%E2%80%A2%20Group%20Analytics&descAlignY=58&descAlign=50&descSize=18&descColor=8892b0" width="100%"/>

<br/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=20&pause=1000&color=00D9FF&center=true&vCenter=true&width=700&lines=Hybrid+Bot+API+%2B+Telethon+Userbot;Deep+OSINT+on+any+Telegram+entity;Real-time+Group+Tracking+%26+Profiling;Username+%26+ID+History+via+SangMata;Paginated+inline+menus+%E2%80%94+zero+clutter)](https://git.io/typing-svg)

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-0a192f?style=for-the-badge&logo=python&logoColor=00d9ff&labelColor=0a192f)
![Telethon](https://img.shields.io/badge/Telethon-1.36+-0a192f?style=for-the-badge&logo=telegram&logoColor=00d9ff&labelColor=0a192f)
![PTB](https://img.shields.io/badge/python--telegram--bot-21+-0a192f?style=for-the-badge&logo=telegram&logoColor=64ffda&labelColor=0a192f)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-0a192f?style=for-the-badge&logo=sqlite&logoColor=ccd6f6&labelColor=0a192f)
![Docker](https://img.shields.io/badge/Docker-Ready-0a192f?style=for-the-badge&logo=docker&logoColor=00d9ff&labelColor=0a192f)
![License](https://img.shields.io/badge/License-MIT-0a192f?style=for-the-badge&logo=opensourceinitiative&logoColor=64ffda&labelColor=0a192f)
![Status](https://img.shields.io/badge/Status-Active-0a192f?style=for-the-badge&logo=statuspage&logoColor=64ffda&labelColor=0a192f)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-ffdd00?style=for-the-badge&logo=buymeacoffee&logoColor=000)](https://buymeacoffee.com/florvex)

<br/>

> **A dual-engine Telegram intelligence bot.**  
> Combines the official Bot API with a Telethon userbot to surface data  
> no standard bot can reach — DC IDs, mutual groups, full flag sets, ID history.

<br/>

</div>

---

## 📌 Table of Contents

<div align="center">

| | Section |
|:---:|:---|
| 🎯 | [What is this?](#-what-is-this) |
| ⚡ | [Features](#-features) |
| 🛠️ | [Requirements](#️-requirements) |
| 📦 | [Installation](#-installation) |
| ⚙️ | [Configuration](#️-configuration) |
| 🚀 | [Running the bot](#-running-the-bot) |
| 📱 | [Commands](#-commands-reference) |
| 📂 | [Project structure](#-project-structure) |
| 🗄️ | [Database schema](#️-database-schema) |
| 🐛 | [Troubleshooting](#-troubleshooting) |
| 🔒 | [Security & Privacy](#-security--privacy) |

</div>

---

## 🎯 What is this?

This bot combines **two Telegram clients running in parallel** to collect data that neither alone could access:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HYBRID ARCHITECTURE                             │
│                                                                     │
│  ┌──────────────────────┐       ┌─────────────────────────────┐    │
│  │  python-telegram-bot │       │     Telethon Userbot        │    │
│  │  (Official Bot API)  │  +    │  (Runs as a real account)   │    │
│  │                      │       │                             │    │
│  │  • /commands         │       │  • Datacenter ID            │    │
│  │  • Inline keyboards  │       │  • Mutual groups            │    │
│  │  • Group logging     │       │  • Full MTProto data        │    │
│  │  • Paginated menus   │       │  • Phone (if public)        │    │
│  │  • /profile /report  │       │  • SangMata ID history      │    │
│  └──────────────────────┘       └─────────────────────────────┘    │
│                         │               │                           │
│                         └──────┬────────┘                           │
│                                ▼                                    │
│               ┌────────────────────────────────┐                   │
│               │   SQLite / PostgreSQL (async)  │                   │
│               │   SQLAlchemy + aiosqlite        │                   │
│               └────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Features

### 🔍 OSINT — Private chat

Look up any Telegram **user**, **group**, or **channel** via username, numeric ID, or `t.me` link.

**User data collected:**

| Field | Notes |
|---|---|
| 🆔 Telegram ID | Permanent numeric identifier |
| 📛 Name | First + last name |
| 🔗 Username | Current handle |
| 📞 Phone | If publicly visible |
| 📝 Bio | Profile description |
| 🌐 Datacenter | DC 1–5 (via Telethon) |
| 🖼️ Photo count | Total profile photos |
| 🕐 Last seen | Online / offline / recently / last week / last month |
| 🌍 Language | Account language code |
| ✨ Emoji status | Premium status emoji |
| 👥 Mutual groups | Shared groups with the userbot |

**Full flag set:**
`Bot · Verified · Premium · Support · Mutual contact · Blocked us · Stories hidden · Require premium · Calls disabled · Scam · Fake · Deleted · Restricted`

**Channel / Group data:**
Title, username, member count, description, DC, reactions, slow mode, sticker pack, geo location, linked chat, invite link, admins list, bots list, banned rights.

---

### 📋 ID & Username History

Query [@SangMata_beta_bot](https://t.me/SangMata_beta_bot) through the userbot — bypasses the forward restriction by polling `iter_messages` instead of forwarding. Returns a clean HTML-formatted history of all recorded name and username changes.

```
/idstorici @username
/idstorici 123456789
```

---

### 👥 Group Tracking — add bot as admin

The bot silently logs all messages and builds rich per-user profiles over time.

**`/report`** — 30-day group analytics:
- Total messages and unique active users
- Top 10 members by message volume (with medals 🥇🥈🥉)

**`/profile`** — deep per-user report (5 pages):
1. **Identity** — ID, name, username, bot/premium flags, first/last seen, days active, total messages
2. **Message stats** — text vs media, mentions, hashtags, average length, replies sent/received
3. **Active hours** — top 5 hours ranked with time-of-day emoji
4. **Interactions** — who they reply to most / who replies to them most
5. **Recent messages** — last 5 messages with timestamps and reply context

---

### 🎛️ Paginated inline menus

Every result is split into pages — no message ever exceeds Telegram's character limit. Navigation is entirely via inline buttons:

```
  ◀ Back     Next ▶
      🏠 Home
```

The bot edits a **single persistent message** — no spam, no noise.

---

## 🛠️ Requirements

- **Python 3.11+**
- A Telegram **Bot Token** → [@BotFather](https://t.me/BotFather)
- A Telegram **API ID + API Hash** → [my.telegram.org](https://my.telegram.org)
- A **Telethon session string** for the userbot account (generated once via `generate_session.py`)

---

## 📦 Installation

### 1. Clone

```bash
git clone https://github.com/your-username/telegram-osint-bot.git
cd telegram-osint-bot
```

### 2. Create a virtual environment

```bash
# Linux / macOS
python3 -m venv venv && source venv/bin/activate

# Windows
python -m venv venv && venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt`:
```
python-telegram-bot>=21.0
telethon>=1.36
sqlalchemy>=2.0
aiosqlite>=0.19
python-dotenv>=1.0
```

### 4. Configure `.env` → [see below](#️-configuration)

### 5. Run

```bash
python main.py
```

The database is created automatically on first run.

---

## ⚙️ Configuration

Create a `.env` file in the project root — **never commit this file**.

```env
# ── Official Bot API ──────────────────────────────
BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef

# ── Telethon Userbot ──────────────────────────────
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890

# Session string — run generate_session.py to get this
# Leave empty to trigger interactive login on first run
USERBOT_STRING_SESSION=

# ── Database ──────────────────────────────────────
# SQLite (default, zero config)
DATABASE_URL=sqlite+aiosqlite:///data.db

# PostgreSQL (production)
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/osintbot
```

<details>
<summary>🔑 How to get BOT_TOKEN</summary>

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Follow the prompts and copy the token

</details>

<details>
<summary>🔑 How to get API_ID and API_HASH</summary>

1. Go to **[my.telegram.org](https://my.telegram.org)**
2. Log in with the phone number of the account that will be the userbot
3. Click **API development tools**
4. Fill in the form (any app name works)
5. Copy `api_id` and `api_hash`

</details>

<details>
<summary>🔑 How to generate USERBOT_STRING_SESSION</summary>

```bash
python generate_session.py
```

Enter your phone number and the OTP Telegram sends you. The script prints a long session string — paste it into `.env` as `USERBOT_STRING_SESSION=`.

> ⚠️ Use a secondary account if possible. The userbot acts as a real Telegram user.

</details>

---

## 🚀 Running the bot

### Local

```bash
python main.py
```

### As a systemd service (Linux VPS)

```bash
sudo nano /etc/systemd/system/osintbot.service
```

```ini
[Unit]
Description=Telegram OSINT Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/telegram-osint-bot
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable osintbot
sudo systemctl start osintbot
sudo journalctl -u osintbot -f
```

### With screen (quick & simple)

```bash
screen -S osintbot
python main.py
# Ctrl+A then D to detach
```

---

## 📱 Commands Reference

### Private chat

| Command | Description |
|---|---|
| `/start` | Open the main menu |
| `/info <target>` | Full OSINT lookup — user, group or channel |
| `/osint <target>` | Alias for `/info` |
| `/idstorici <target>` | Username / ID change history |

`<target>` accepts: `@username` · `123456789` · `https://t.me/username`

### Groups (bot must be admin)

| Command | Description |
|---|---|
| `/report` | Group analytics — last 30 days |
| `/profile <target>` | Deep profile of a group member |
| `/profile` *(reply to message)* | Profile of the message author |

---

## 📂 Project Structure

```
.
├── main.py               # Entry point — starts DB, userbot, PTB app loop
├── config.py             # Reads .env and exposes typed constants
├── bot_handlers.py       # All PTB handlers + paginated UI engine
├── osint.py              # collect_osint_data() — core OSINT collector
├── sangmata.py           # SangMata poller + Markdown→HTML formatter
├── userbot_client.py     # Telethon wrapper — shared singleton
├── analytics.py          # Group report queries (SQLAlchemy)
├── user_profiling.py     # Per-user profile queries and data assembly
├── database.py           # ORM models + init_db() + get_session()
├── generate_session.py   # Interactive session string generator
└── .env                  # Your secrets — never commit
```

---

## 🗄️ Database Schema

| Table | Contents |
|---|---|
| `message_logs` | Raw messages: chat, user, date, text |
| `message_metadata` | Rich metadata: media type, reply chain, mentions, hashtags, text length |
| `user_profiles` | Username, display name, bot/premium flags, last updated |
| `user_activity` | Per-chat message count, first seen, last seen |
| `user_interactions` | Reply counts between users (interaction graph) |
| `groups` | Registered groups |

The schema is created automatically on first run. To switch to PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/osintbot
```

```bash
pip install asyncpg
```

---

## 🐛 Troubleshooting

<details>
<summary>❌ "BOT_TOKEN not set"</summary>

Check that `.env` is in the project root and that there are no spaces around `=`.

</details>

<details>
<summary>❌ Userbot won't start / session invalid</summary>

Delete the old session and regenerate:
```bash
python generate_session.py
```
Paste the new string into `.env`.

</details>

<details>
<summary>❌ get_chat_history / Pyrogram errors</summary>

This project uses **Telethon**, not Pyrogram. If you see Pyrogram-related errors, you may be running an old version of the files. Pull the latest code and verify that `userbot_client.py` imports from `telethon`.

</details>

<details>
<summary>❌ "message to edit not found"</summary>

Expected — if the menu message was deleted, the bot sends a new one automatically. No action needed.

</details>

<details>
<summary>❌ /report is slow on large groups</summary>

Switch to PostgreSQL, or reduce the report window:
```python
pages = await _build_report_pages(chat.id, days=7)
```

</details>

---

## 🔒 Security & Privacy

> ⚠️ **This tool collects and stores data about Telegram users.**  
> Only deploy in groups where members are informed of data collection.  
> Comply with GDPR, your local privacy laws, and Telegram's Terms of Service.

- **Never commit `.env`** — add it to `.gitignore`
- The session string is equivalent to full account access — treat it as a password
- `data.db` contains all logged messages — restrict access and back it up regularly
- The bot only logs messages in groups **where it has been added as administrator**

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

PRs are welcome. Please open an issue first for major changes.

```bash
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
# Open a Pull Request
```

---

<div align="center">

[![Telegram](https://img.shields.io/badge/Telegram-Channel-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/florvexchannel)

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d0d0d,30:0a192f,60:112240,100:1a1a2e&height=100&section=footer" width="100%"/>

**If this project was useful, consider leaving a ⭐**

[⬆ Back to top](#-telegram-osint-bot)

</div>
