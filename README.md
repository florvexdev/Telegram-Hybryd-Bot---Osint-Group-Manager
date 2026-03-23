<div align="center">

<!-- Animated Header Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:203a43,100:2c5364&height=200&section=header&text=Telegram%20Hybrid%20Bot&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=OSINT%20%E2%80%A2%20Intelligence%20%E2%80%A2%20Group%20Analytics&descAlignY=55&descAlign=50" width="100%"/>

<br/>

<!-- Animated typing effect badge -->
[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=00D9FF&center=true&vCenter=true&width=600&lines=Advanced+Telegram+OSINT+Bot;Hybrid+API+%2B+Userbot+Architecture;Real-time+Group+Analytics;Deep+User+Profiling+%26+Intelligence)](https://git.io/typing-svg)

<br/>

<!-- Badges Row 1 -->
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0-00B2FF?style=for-the-badge&logo=telegram&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<!-- Badges Row 2 -->
![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge&logo=opensourceinitiative&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge&logo=statuspage&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlite&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-aiosqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

<br/>

> **A powerful hybrid Telegram bot combining OSINT intelligence, real-time user tracking,  
> and group analytics — built on dual API architecture for maximum data depth.**

<br/>

</div>

---

## 📌 Table of Contents

<div align="center">

| Section | Description |
|:---:|:---|
| [🎯 What is this?](#-what-is-this) | Project overview and architecture |
| [⚡ Core Features](#-core-features) | Full feature breakdown |
| [🛠️ Requirements](#️-requirements) | Software & account prerequisites |
| [📦 Installation](#-installation) | Step-by-step setup guide |
| [⚙️ Configuration](#️-configuration) | `.env` variables and credentials |
| [🚀 Hosting Options](#-hosting-options) | Local, VPS, Docker, systemd |
| [📱 Commands Reference](#-commands-reference) | All bot commands explained |
| [📂 Project Structure](#-project-structure) | File-by-file architecture guide |
| [📊 Profiling System](#-profiling-system) | What data is collected and how |
| [🗄️ Database Schema](#️-database-schema) | Tables, fields, and relationships |
| [🐛 Troubleshooting](#-troubleshooting) | Common issues and fixes |
| [🔒 Security & Privacy](#-security--privacy) | Legal considerations & best practices |
| [☕ Support the Project](#-support-the-project) | Ways to contribute |

</div>

---

## 🎯 What is this?

**Telegram Hybrid Bot** is not just another bot — it's a **dual-engine intelligence platform** that leverages *both* the official Telegram Bot API and a Pyrogram userbot client simultaneously.

This hybrid approach unlocks data that is simply inaccessible from a regular bot alone:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      HYBRID ARCHITECTURE                                │
│                                                                         │
│   ┌─────────────────────┐        ┌──────────────────────────────┐       │
│   │   Official Bot API  │        │      Pyrogram Userbot        │       │
│   │  (python-telegram-  │   +    │   (Acts as a real account)   │       │
│   │       bot)          │        │                              │       │
│   │                     │        │  • Datacenter ID             │       │
│   │  • Commands (/info) │        │  • Common groups             │       │
│   │  • Group tracking   │        │  • Extended profile data     │       │
│   │  • Message handling │        │  • Username history          │       │
│   │  • Inline buttons   │        │  • Phone number (if public)  │       │
│   └─────────────────────┘        └──────────────────────────────┘       │
│                          │                │                              │
│                          └────────┬───────┘                              │
│                                   ▼                                     │
│                     ┌─────────────────────────┐                         │
│                     │   SQLite / PostgreSQL   │                         │
│                     │     Async Database      │                         │
│                     │  (SQLAlchemy + asyncio) │                         │
│                     └─────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**The result?** A complete intelligence and monitoring system that builds rich user profiles over time, generates group activity reports, and surfaces OSINT data on any Telegram user.

---

## ⚡ Core Features

### 🔍 OSINT — User Intelligence

Look up any Telegram user and get a full profile in seconds. Supports multiple input formats:

```
/info @username
/info 123456789
/info https://t.me/username
```

Data returned for each user:

| Field | Description |
|---|---|
| 🆔 Telegram ID | Permanent numeric identifier |
| 👤 Full Name | First + Last name |
| 🔗 Username | Current public handle |
| 📞 Phone Number | If publicly visible |
| 📝 Bio | Profile description |
| 🖼️ Profile Photo | Current avatar |
| 🌐 Datacenter ID | Server location (via userbot) |
| ✅ Account Status | Bot / Premium / Verified / Disabled |
| 👥 Common Groups | Shared groups with the userbot account |

---

### 🕵️ Username & ID History

Track past identities of any user. Due to userbot integration, the bot can query external databases for historical usernames and detect account ID changes over time.

```
/idstorici @username
/idstorici 123456789
```

---

### 📊 Group Monitoring & Activity Reports

Add the bot as administrator in any group — it will silently collect activity data and let you generate detailed reports on demand.

```
/report   →  Full 30-day group analytics report
```

Report includes:
- 📈 Total message count (by user and overall)
- 🏆 Most active members ranking
- 🕐 Peak activity hours
- 🖼️ Media breakdown (photos, videos, docs, voice, audio)
- **#️⃣** Most used hashtags
- **@** Most mentioned users

---

### 👤 Deep User Profiling

The bot builds a persistent profile for every user it encounters in monitored groups:

```
/profile @username
/profile 123456789
/profile              ← reply to any message
```

Profile data includes personal info, account status, technical metadata, and full activity timeline within the group.

---

### 🔄 Interaction Graph

Beyond individual stats, the bot maps **who talks to whom**:
- Reply chains (who responds to whom)
- Mention relationships
- Interaction frequency and timestamps

This creates a social graph of the group over time.

---

## 🛠️ Requirements

### System

| Platform | Support |
|---|---|
| 🐧 Linux | ✅ Recommended for production |
| 🪟 Windows | ✅ Supported (ideal for development) |
| 🍎 macOS | ✅ Fully supported |

### Software

- **Python 3.11+** — required
- **pip** — Python package manager
- **Docker + Docker Compose** — optional, for containerized deployment

### Telegram Credentials

You will need **three** things from Telegram:

> #### 1. Bot Token — from @BotFather
> Used by the official Bot API engine.
>
> #### 2. API ID + API Hash — from my.telegram.org
> Used by the Pyrogram userbot client.
>
> #### 3. Userbot Session String *(optional but recommended)*
> Unlocks extended OSINT capabilities. Generated via `generate_session.py`.

---

## 📦 Installation

### Option A — Local Python Install

**Step 1: Clone the repo**
```bash
git clone https://github.com/yourusername/telegram_hybrid_bot.git
cd telegram_hybrid_bot
```

**Step 2: Create a virtual environment**
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

**Step 3: Install dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

<details>
<summary>📋 View main dependencies</summary>

| Package | Version | Purpose |
|---|---|---|
| `python-telegram-bot[job-queue]` | 20.7 | Official Telegram Bot API |
| `pyrogram` | 2.0.106 | Userbot client (OSINT engine) |
| `tgcrypto` | 1.2.5 | Telegram encryption layer |
| `sqlalchemy[asyncio]` | 2.0.23 | Async ORM framework |
| `aiosqlite` | 0.19.0 | Async SQLite driver |
| `python-dotenv` | 1.0.0 | `.env` variable loader |

</details>

**Step 4: Configure your `.env` file** ← [see Configuration section](#️-configuration)

**Step 5: Run**
```bash
python main.py
```

---

### Option B — Docker Compose

```bash
git clone https://github.com/yourusername/telegram_hybrid_bot.git
cd telegram_hybrid_bot

# Create and fill your .env file
nano .env

# Start everything
docker-compose up -d

# Watch logs
docker-compose logs -f bot

# Stop
docker-compose down
```

---

## ⚙️ Configuration

Create a file named `.env` in the root of the project. This file holds all secrets — **never commit it to Git**.

```env
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 BOT — Official Telegram API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👤 USERBOT — Pyrogram Client
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890

# Session string generated by generate_session.py
# Leave empty to trigger interactive login on first run
USERBOT_STRING_SESSION=

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗄️ DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# SQLite (default, zero config)
DATABASE_URL=sqlite+aiosqlite:///data.db

# PostgreSQL (for production scale)
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/telegram_bot
```

---

### How to get each credential

<details>
<summary>🔑 BOT_TOKEN — step by step</summary>

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Give your bot a name (e.g. `My OSINT Bot`)
4. Give it a username ending in `bot` (e.g. `myosint_bot`)
5. Copy the token in the format `123456:ABCdef...`
6. Paste it as `BOT_TOKEN=` in your `.env`

</details>

<details>
<summary>🔑 API_ID & API_HASH — step by step</summary>

1. Go to **[my.telegram.org](https://my.telegram.org)**
2. Log in with your phone number (same account that will be the userbot)
3. Click **"API development tools"**
4. Fill in the form (any name/description is fine)
5. Copy your `App api_id` → `API_ID=`
6. Copy your `App api_hash` → `API_HASH=`

</details>

<details>
<summary>🔑 USERBOT_STRING_SESSION — step by step</summary>

This is optional but unlocks the full OSINT capabilities.

```bash
# Make sure API_ID and API_HASH are already in your .env
python generate_session.py
```

The script will:
1. Ask for your phone number
2. Send a Telegram verification code to your account
3. Ask you to enter the code
4. Generate a long session string

Copy that string into `.env` as `USERBOT_STRING_SESSION=`.

> ⚠️ **Important:** Use a secondary Telegram account if possible. The userbot acts as a real user.

</details>

---

## 🚀 Hosting Options

### 🖥️ Option 1 — Local (Development)

```bash
source venv/bin/activate
python main.py
```

> ✅ Zero cost, easy debugging  
> ❌ Bot goes offline when your machine shuts down

---

### ☁️ Option 2 — VPS (Production Recommended)

Affordable 24/7 hosting. Recommended providers:

| Provider | Starting Price | Notes |
|---|---|---|
| [Hetzner](https://hetzner.com) | ~€4/month | Best value in Europe |
| [Vultr](https://vultr.com) | ~$2.50/month | Cheap US options |
| [DigitalOcean](https://digitalocean.com) | ~$5/month | Great docs & UX |
| [Linode](https://linode.com) | ~$5/month | Reliable & fast |
| [AWS EC2](https://aws.amazon.com) | Free tier | 12 months free |

**Setup on Ubuntu 22.04:**
```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# System update
apt update && apt upgrade -y
apt install -y python3.11 python3-pip python3-venv git

# Clone and install
git clone https://github.com/yourusername/telegram_hybrid_bot.git
cd telegram_hybrid_bot
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# Configure
nano .env

# Run persistently with screen
screen -S bot
python main.py
# Ctrl+A then D to detach
```

---

### 🐳 Option 3 — Docker on VPS (Advanced)

Best for isolation, easy updates, and clean deployments:

```bash
git clone https://github.com/yourusername/telegram_hybrid_bot.git
cd telegram_hybrid_bot
nano .env
docker-compose up -d

# Update the bot later:
docker-compose down
git pull origin main
docker-compose up -d --build
```

---

### 🔁 Option 4 — systemd Service (Auto-restart on reboot)

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

```ini
[Unit]
Description=Telegram Hybrid Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/telegram_hybrid_bot
Environment="PATH=/root/telegram_hybrid_bot/venv/bin"
ExecStart=/root/telegram_hybrid_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Monitor
sudo systemctl status telegram-bot
sudo journalctl -u telegram-bot -f
```

---

### ☁️ Option 5 — Cloud Platforms (Render / Railway / Fly.io)

Platforms like Render, Railway, and Fly.io work well with the included `Dockerfile`. Just:
1. Push the repo to GitHub
2. Connect it to the platform
3. Set environment variables in their dashboard
4. Deploy

---

## 📱 Commands Reference

### 💬 Private Chat (Direct Messages)

| Command | Description |
|---|---|
| `/start` | Opens the interactive main menu with buttons |
| `/info <user>` | Full OSINT profile lookup for any user |
| `/idstorici <user>` | View historical usernames and ID changes |

**`/info` supports:**
```
/info @username
/info 123456789
/info https://t.me/username
```

---

### 👥 In Groups (Admin required)

| Command | Description |
|---|---|
| `/report` | 30-day group analytics report |
| `/profile <user>` | Full profile of a group member |

**`/profile` supports:**
```
/profile @username
/profile 123456789
/profile             ← reply to someone's message
```

---

### 🖱️ Interactive Menu Buttons

The bot also provides an inline button interface accessible via `/start`:

| Button | Action |
|---|---|
| 🔍 Search User | Launches OSINT user lookup |
| 📋 ID History | Checks historical username records |
| 📖 Help | Shows full usage guide |

---

## 📂 Project Structure

```
telegram_hybrid_bot/
│
├── 🚀 main.py                  # Entry point — initializes DB, userbot & bot, starts event loop
├── ⚙️  config.py               # Loads .env variables and makes them available globally
├── 📋 requirements.txt         # All Python dependencies
│
├── 🗄️  database.py             # SQLAlchemy async models: User, Group, Messages, Interactions
├── 🤖 bot_handlers.py          # All Telegram command handlers & inline button callbacks
├── 👤 userbot_client.py        # Pyrogram wrapper — powers OSINT data extraction
├── 🔍 osint.py                 # Core OSINT logic: user search, data collection & formatting
├── 📊 analytics.py             # Group report generation and statistics aggregation
├── 🧠 user_profiling.py        # Profile building, formatting, and data retrieval
├── 🗂️  sangmata.py             # Integration with Sangmata API for ID/username history
│
├── 🔧 generate_session.py      # Utility: generates Pyrogram session string interactively
│
├── 🐳 Dockerfile               # Docker image definition
├── 🐳 docker-compose.yml       # Multi-container orchestration config
│
├── 📖 PROFILING_GUIDE.md       # Detailed guide on the profiling system
│
├── data/
│   └── 💾 data.db              # SQLite database (auto-generated at first run)
│
└── 🔒 .env                     # ← YOUR SECRETS — never commit this file!
```

---

## 📊 Profiling System

When the bot is an admin in a group, it automatically tracks every message without interfering with the conversation. Here's what gets recorded:

### 👤 Personal Data
```
• Current username and display name
• Profile bio text
• Profile photo URL
• Account flags: is_bot / is_premium / is_verified
• Phone number (if publicly visible)
• Datacenter ID (via userbot)
```

### 📈 Activity Data
```
• Total messages sent in the group
• First seen timestamp (when they first appeared)
• Last seen timestamp (most recent message)
• Activity patterns by hour
```

### 💬 Message Metadata
```
• Message ID and chat ID
• Reply target: message ID + user ID
• Media type: photo / video / document / audio / voice
• Text length
• Contains @mention: yes/no
• Contains #hashtag: yes/no
```

### 🔗 Interaction Graph
```
• From user → To user (reply or mention)
• Interaction type: reply / mention / quote
• Total interaction count
• Timestamp of last interaction
```

---

## 🗄️ Database Schema

The bot uses **SQLAlchemy async** with either **SQLite** (default) or **PostgreSQL**.

<details>
<summary>📋 View full schema</summary>

#### `groups`
```
id          PK
chat_id     BigInteger  UNIQUE
title       String
added_at    DateTime
is_active   Boolean
```

#### `user_profiles`
```
id                  PK
user_id             BigInteger  UNIQUE
username            String
first_name          String
last_name           String
bio                 Text
profile_photo_url   String
is_bot              Boolean
is_premium          Boolean
phone               String
dc_id               Integer
updated_at          DateTime
```

#### `message_logs`
```
id          PK
chat_id     BigInteger  INDEXED
user_id     BigInteger  INDEXED
date        DateTime
message_id  Integer
text        Text
```

#### `user_activity`
```
id              PK
user_id         BigInteger  INDEXED
chat_id         BigInteger  INDEXED
total_messages  Integer
first_seen      DateTime
last_seen       DateTime
```

#### `message_metadata`
```
id                  PK
chat_id             BigInteger  INDEXED
message_id          Integer     INDEXED
user_id             BigInteger  INDEXED
reply_to_message_id Integer
reply_to_user_id    BigInteger
media_type          String
text_length         Integer
has_mention         Boolean
has_hashtag         Boolean
```

#### `user_interactions`
```
id                PK
from_user_id      BigInteger  INDEXED
to_user_id        BigInteger  INDEXED
interaction_type  String
count             Integer
last_interaction  DateTime
```

</details>

### Switch to PostgreSQL

For large groups or high-volume tracking, switch to PostgreSQL for better performance:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/telegram_bot
```

```bash
pip install asyncpg
```

---

## 🐛 Troubleshooting

<details>
<summary>❌ "BOT_TOKEN not set in .env file"</summary>

- Check the `.env` file exists in the **project root** (not inside a subfolder)
- Ensure there are **no spaces** around `=`: use `BOT_TOKEN=xxx` not `BOT_TOKEN = xxx`
- Make sure the token format is correct: `123456789:ABCdef...`

</details>

<details>
<summary>❌ "API_ID not set" or "API_HASH not set"</summary>

- Go to [my.telegram.org](https://my.telegram.org) and log in
- Navigate to "API development tools"
- Copy the values **exactly** — no extra spaces

</details>

<details>
<summary>❌ Userbot won't connect</summary>

If you don't have a session string yet:
```bash
python generate_session.py
```
Follow the prompts, then paste the result into `.env` as `USERBOT_STRING_SESSION=`.

</details>

<details>
<summary>❌ "message_to_edit not found"</summary>

This is **expected behavior**. The bot tries to edit a previous status message. If it can't find it, it creates a new one automatically. No action needed.

</details>

<details>
<summary>❌ Database locked</summary>

```bash
# Stop the bot first, then:
rm data.db
python main.py   # A fresh database will be created
```

</details>

<details>
<summary>❌ Docker: "Connection refused"</summary>

```bash
docker-compose down
docker-compose up -d --build
docker-compose logs -f
```

Make sure `.env` exists and contains valid credentials before building.

</details>

<details>
<summary>❌ /report is very slow</summary>

- Your database is likely large. Consider switching to **PostgreSQL**
- Add composite indexes on frequently queried columns
- Reduce the report window (e.g., last 7 days instead of 30)
- Implement periodic archiving of old data:

```python
from datetime import datetime, timedelta

async with get_session() as session:
    cutoff = datetime.utcnow() - timedelta(days=90)
    await session.execute(delete(MessageLog).where(MessageLog.date < cutoff))
    await session.commit()
```

</details>

---

## 🔒 Security & Privacy

> ⚠️ **Legal Notice**  
> This bot collects and stores data about Telegram users. Before deploying in any group, ensure you have:
> - Informed consent from monitored users
> - Compliance with applicable privacy laws (GDPR, CCPA, etc.)
> - A clear data collection and retention policy

### Best Practices

- 🔐 **Never share `.env`** — add it to `.gitignore` immediately
- 🔄 **Rotate tokens** if you suspect a leak (via @BotFather and my.telegram.org)
- 🧹 **Backup regularly** — `data.db` is your entire dataset
- 🔒 **Use HTTPS** — if exposing via webhook instead of polling
- 📦 **Keep dependencies updated**:
  ```bash
  pip install --upgrade -r requirements.txt
  ```

---

## 📚 Resources

| Resource | Link |
|---|---|
| python-telegram-bot docs | [python-telegram-bot.readthedocs.io](https://python-telegram-bot.readthedocs.io/) |
| Pyrogram docs | [docs.pyrogram.org](https://docs.pyrogram.org/) |
| SQLAlchemy docs | [docs.sqlalchemy.org](https://docs.sqlalchemy.org/) |
| Telegram Bot API Reference | [core.telegram.org/bots/api](https://core.telegram.org/bots/api) |
| Telegram Client API | [core.telegram.org/methods](https://core.telegram.org/methods) |

---

## 🤝 Contributing

Contributions are welcome and appreciated!

```bash
# 1. Fork the repo
# 2. Create your feature branch
git checkout -b feature/AmazingFeature

# 3. Commit your changes
git commit -m 'Add AmazingFeature'

# 4. Push to your branch
git push origin feature/AmazingFeature

# 5. Open a Pull Request
```

Please make sure your code follows the existing style and includes appropriate comments.

---

## ☕ Support the Project

If this bot saves you time or is useful for your projects, please consider supporting its development!

<div align="center">

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20Development-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/florvex)

</div>

### Other ways to support

- ⭐ **Star this repository** — it helps others discover the project
- 🐛 **Report bugs** — open an issue with steps to reproduce
- 💡 **Suggest features** — via GitHub Discussions
- 🔗 **Share** — tell your community about it



## 📝 Changelog

| Version | Date | Highlights |
|---|---|---|
| v1.0 | 2024 | Initial release — OSINT core + basic tracking |
| v1.1 | 2024 | Advanced profiling system |
| v1.2 | 2024 | Group reports & analytics engine |
| v1.3 | 2024 | Docker support + containerization |

---

## 📄 License

This project is distributed under the **MIT License**.  
See the [`LICENSE`](./LICENSE) file for full details.

---

## 🔗 Contacts

<div align="center">

[![Telegram](https://img.shields.io/badge/Telegram-@florvexchannel-26A5E4?style=for-the-badge&logo=telegram)](https://t.me/florvexchannel)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/florvex)

</div>

---

## 🙏 Acknowledgments

- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)** — for the solid and well-documented Bot API wrapper
- **[Pyrogram](https://github.com/pyrogram/pyrogram)** — for enabling userbot-level access to Telegram's MTProto API
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — for the flexible and powerful async ORM
- **The Telegram community** — for continuous feedback and support

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:203a43,100:2c5364&height=100&section=footer" width="100%"/>

**Made with ❤️ — If this project helped you, consider giving it a ⭐**

[⬆ Back to top](#-telegram-hybrid-bot)

</div>
