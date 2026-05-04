<div align="center">

<img src="https://raw.githubusercontent.com/gavrielc/nanoclaw/main/assets/nanoclaw-logo.png" alt="NanoClaw" width="200"/>

# nanoclaw-py

**Build Your Personal AI Agent in ~500 Lines of Python**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Claude Code SDK](https://img.shields.io/badge/Claude_Code_SDK-Anthropic-cc785c?style=flat-square&logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code-sdk)
[![Telegram Bot API](https://img.shields.io/badge/Telegram_Bot_API-v22-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://python-telegram-bot.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/ApeCodeAI/nanoclaw-py?style=flat-square&logo=github)](https://github.com/ApeCodeAI/nanoclaw-py/stargazers)
[![ApeCode.ai](https://img.shields.io/badge/🦧_ApeCode.ai-AI_Tools-orange?style=flat-square)](https://apecode.ai)
[![ApeRouter](https://img.shields.io/badge/🔗_ApeRouter-LLM_API-blue?style=flat-square)](https://apecode.ai/products/aperouter)

<p>
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#%EF%B8%8F-configuration">Configuration</a> •
  <a href="#-faq">FAQ</a> •
  <a href="#-中文文档">中文</a>
</p>

</div>

---

## What is this?

**nanoclaw-py** is a personal AI Agent powered by the **Claude Code SDK**, communicating with you via **Telegram**. It can read/write files, execute commands, search the web, and schedule tasks — all in **~500 lines of Python**.

nanoclaw-py is its Python rewrite with Telegram as the messaging channel (instead of WhatsApp) and a focus on simplicity. This project is part of the [ApeCode.ai](https://apecode.ai) learning series.
> This project is heavily inspired by [**nanoclaw**](https://github.com/gavrielc/nanoclaw) — a brilliant, minimal Claude agent by [@gavrielc](https://github.com/gavrielc). 

```
You: @Ape Write a Python script to scrape Hacker News headlines
Ape: Sure, let me create that script...
     ✅ Created workspace/hn_scraper.py

You: @Ape Run it every day at 9am and send me the results
Ape: ✅ Scheduled task created (cron: 0 9 * * *)
     I'll run the script and send you results daily at 9:00
```

### Data Flow

<div align="center">
<img src="./assets/architecture.svg" alt="Architecture Diagram" width="800"/>
</div>

## ✨ Features

| Capability | Description |
|------------|-------------|
| **Natural Language** | Powered by Claude Code SDK, understands complex instructions |
| **File Operations** | Read, write, and edit files in the workspace |
| **Command Execution** | Run Bash commands and Python scripts |
| **Web Search** | Built-in WebSearch / WebFetch tools |
| **Task Scheduling** | Cron / interval / one-time tasks with proactive notifications |
| **Long-term Memory** | CLAUDE.md persists user preferences across sessions |
| **Conversation History** | Daily archives in `conversations/` folder, searchable by Agent |
| **Session Continuity** | Auto-restore conversation context after restart |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Anthropic API Key

### 1. Clone the repo

```bash
git clone https://github.com/ApeCodeAI/nanoclaw-py.git
cd nanoclaw-py
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token      # From @BotFather
OWNER_ID=your_telegram_user_id          # From @userinfobot
ANTHROPIC_API_KEY=sk-ant-api03-...      # Your Anthropic API Key
```

> **Need an Anthropic API Key?** You can get one at [moacode.org](https://moacode.org/register?ref=bbruceyu), which provides Anthropic API access with a friendly interface.

> 💡 **Need an Anthropic API key?** [ApeRouter](https://apecode.ai/products/aperouter) provides a reliable LLM API proxy — no VPN needed for users in China. Supports Claude, GPT, Kimi and more.

### 4. Run

```bash
uv run python -m nanoclaw
```

Open Telegram, send a message to your bot, and start chatting!

## 🏗 Architecture

```
src/nanoclaw/           533 lines of code (9 files)
├── __main__.py          52 lines  ← Entry point
├── config.py            50 lines  ← Environment variables & paths
├── db.py               114 lines  ← SQLite async operations (tasks only)
├── memory.py            44 lines  ← CLAUDE.md long-term memory
├── agent.py            210 lines  ← Claude Code SDK + 6 MCP tools
├── scheduler.py         75 lines  ← APScheduler task execution
├── bot.py               69 lines  ← Telegram Bot handlers
└── conversations.py     69 lines  ← Daily conversation archiving
```

### MCP Tools

The Agent interacts with Telegram and the scheduler through these MCP tools:

| Tool | Purpose |
|------|---------|
| `send_message` | Proactively send messages (during tasks/long operations) |
| `schedule_task` | Create scheduled tasks (cron/interval/once) |
| `list_tasks` | List all scheduled tasks |
| `pause_task` | Pause a task |
| `resume_task` | Resume a paused task |
| `cancel_task` | Delete a task |

## ⚙️ Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Telegram Bot Token |
| `OWNER_ID` | ✅ | — | Your Telegram user ID |
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API Key |
| `ANTHROPIC_BASE_URL` | — | Official | Custom API endpoint (proxy/gateway) |
| `ASSISTANT_NAME` | — | `Ape` | Assistant's name |
| `SCHEDULER_INTERVAL` | — | `60` | Task check interval (seconds) |

> **Custom API Endpoint**: Set `ANTHROPIC_BASE_URL` to route requests through LiteLLM proxy, enterprise gateway, or any Anthropic Messages API compatible endpoint.

## 📂 Data Directories

| Directory | Purpose | Persistent |
|-----------|---------|------------|
| `workspace/` | Agent's working directory for file operations | ✅ |
| `workspace/CLAUDE.md` | Long-term memory (preferences, facts) | ✅ |
| `workspace/conversations/` | Daily chat archives (YYYY-MM-DD.md) | ✅ |
| `store/nanoclaw.db` | SQLite database (scheduled tasks only) | ✅ |
| `data/state.json` | Session ID for conversation continuity | ✅ |

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message |
| `/clear` | Clear current session, start fresh |
| Any text | Chat with the AI |

## ❓ FAQ

<details>
<summary><b>How do I get my Telegram user ID?</b></summary>

Search for `@userinfobot` on Telegram and send any message. It will reply with your user ID.

</details>

<details>
<summary><b>Why single-user only?</b></summary>

This is an educational project. The `OWNER_ID` restriction ensures only you can use it. The Agent has Bash execution privileges — exposing it publicly would be a security risk.

</details>

<details>
<summary><b>Does the session persist after restart?</b></summary>

Yes. Session is persisted via `session_id` in `data/state.json` and auto-restored on restart. Long-term memory in `workspace/CLAUDE.md` survives even `/clear` commands.

</details>

<details>
<summary><b>Do scheduled tasks survive restart?</b></summary>

Yes. Tasks are stored in SQLite and the scheduler automatically picks up due tasks after restart.

</details>

<details>
<summary><b>Can I use a proxy or custom API endpoint?</b></summary>

Yes. Set `ANTHROPIC_BASE_URL` to your proxy address. It must be compatible with the Anthropic Messages API format.

</details>

## 🔒 Security Notice

> **This project is for personal learning and private deployment only.** The Agent can execute arbitrary commands (`bypassPermissions` mode). Do NOT deploy publicly or share access with others.

## 📄 License

[MIT](LICENSE)

---

# 🇨🇳 中文文档

## 这是什么？

**nanoclaw-py** 是一个个人 AI Agent，基于 **Claude Code SDK**，通过 **Telegram** 与你对话。它能读写文件、执行命令、搜索网页、调度定时任务——所有这些，仅用 **~500 行 Python**。

本项目高度参考了 [**nanoclaw**](https://github.com/gavrielc/nanoclaw)——由 [@gavrielc](https://github.com/gavrielc) 开发的极简 Claude Agent 项目。nanoclaw-py 是其 Python 重写版本，使用 Telegram 作为消息通道（而非 WhatsApp），更注重简洁性。

本项目是 [ApeCode.ai](https://apecode.ai) 学习系列的一部分。

```
你: @Ape 帮我写一个 Python 脚本，爬取 Hacker News 首页标题
Ape: 好的，我来创建这个脚本...
     ✅ 已创建 workspace/hn_scraper.py

你: @Ape 每天早上 9 点运行一次，把结果发给我
Ape: ✅ 已创建定时任务 (cron: 0 9 * * *)
     每天 9:00 我会运行脚本并把结果发到这里
```

## 功能特性

| 能力 | 描述 |
|------|------|
| **自然语言对话** | 基于 Claude Code SDK，理解复杂指令 |
| **文件操作** | 在 workspace 中读写、编辑文件 |
| **命令执行** | 运行 Bash 命令、Python 脚本 |
| **网络搜索** | 内置 WebSearch / WebFetch 工具 |
| **定时任务** | Cron / 间隔 / 一次性任务调度，主动推送结果 |
| **长期记忆** | CLAUDE.md 持久化用户偏好，跨会话保留 |
| **对话历史** | 每日归档到 `conversations/` 文件夹，Agent 可搜索 |
| **会话连续** | Session 自动恢复，重启不丢上下文 |

## 快速开始

### 前置条件

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 包管理器
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 已安装
- Telegram Bot Token（[@BotFather](https://t.me/BotFather) 获取）
- Anthropic API Key

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/ApeCodeAI/nanoclaw-py.git
cd nanoclaw-py

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 Token 和 API Key
# 需要 Anthropic API Key？可以在 https://moacode.org/register?ref=bbruceyu 获取

# 4. 启动
uv run python -m nanoclaw
```

打开 Telegram，给你的 Bot 发送消息，开始对话！

### 配置说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Telegram Bot Token |
| `OWNER_ID` | ✅ | — | 你的 Telegram 用户 ID |
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API Key |
| `ANTHROPIC_BASE_URL` | — | 官方 | 自定义 API 端点（代理/网关） |
| `ASSISTANT_NAME` | — | `Ape` | 助手名称 |

> **获取用户 ID**：在 Telegram 搜索 `@userinfobot`，发送任意消息即可获取。

## 常见问题

<details>
<summary><b>可以用国内 API 代理吗？</b></summary>

可以。设置 `ANTHROPIC_BASE_URL` 为你的代理地址即可，需兼容 Anthropic Messages API 格式。

</details>

<details>
<summary><b>重启后会话还在吗？</b></summary>

会话通过 `session_id` 持久化到 `data/state.json`，重启后自动恢复。长期记忆保存在 `workspace/CLAUDE.md`，即使 `/clear` 重置会话也不会丢失。

</details>

<details>
<summary><b>为什么只支持单用户？</b></summary>

这是一个教学项目，通过 `OWNER_ID` 限制只有你自己可以使用。Agent 拥有 Bash 执行权限，开放给公众会有安全风险。

</details>

## 安全提醒

> **本项目仅供个人学习和私有部署使用。** Agent 具有执行任意命令的能力，切勿部署到公网或开放给他人使用。

---

<div align="center">

**If you find this useful, please give it a ⭐!**

**觉得有用？请给个 ⭐ 支持一下！**

Built with ❤️ by [ApeCode.ai](https://apecode.ai)

</div>
