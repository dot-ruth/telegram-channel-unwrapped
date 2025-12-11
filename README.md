# 📊 Telegram Channel Unwrapped Bot

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A powerful Telegram bot that generates **Spotify-Wrapped style summaries** for any public Telegram channel. It analyzes views, reactions, and activity patterns to create beautiful, shareable Glassmorphism visual cards.

> **Original Concept by:** [@dot_ruth](https://github.com/dot-ruth)
>
> **Refactored & Enhanced by:** [@eyuBirhanu](https://github.com/eyuBirhanu)

---

## ✨ Features

- **📅 Check Any Year**: Fetch data for specific years (e.g., `@Telegram 2021`) or defaults to the current year.
- **🎨 Glassmorphism UI**: Generates a modern, dark-themed visual card with sleek transparent elements.
- **📈 Advanced Analytics**:
  - Live Subscriber Count
  - Engagement Rate Calculation
  - Detailed Media Breakdown (Photos, Videos, Polls)
- **⚡ Smart Progress**: Real-time status updates while fetching and processing thousands of messages.

---

## 🚀 Getting Started

### 1. Prerequisites

Before you begin, ensure you have the following:

- **Python 3.9** or higher installed.
- **Telegram API Credentials**:
  - Get your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
- **Bot Token**:
  - Create a bot and get the token from [@BotFather](https://t.me/BotFather).

### 2. Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/eyuBirhanu/telegram-channel-unwrapped.git
   cd telegram-channel-unwrapped
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create a `.env` file in the root directory and add your credentials:
   ```ini
   API_ID=123456
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   SESSION_STRING=your_generated_string_session
   ```

### 3. Usage

Run the bot with the following command:

```bash
python main.py
```

#### 🤖 Bot Commands

- `/start` : Initialize the interaction with the bot.
- `@ChannelName` : Generate a summary for the specified channel for the current year.
- `@ChannelName 2023` : Generate a summary for a specific year.

---

## 🛠️ Tech Stack

- **[Telethon](https://docs.telethon.dev/)**: For fetching channel history and subscriber data efficiently.
- **[Python-Telegram-Bot](https://python-telegram-bot.org/)**: For handling user interactions and bot commands.
- **[Pillow (PIL)](https://python-pillow.org/)**: For drawing and generating the analytic image cards.

---

## 📜 License

This project is open-source. Please credit the original author and contributors when forking or using this code.