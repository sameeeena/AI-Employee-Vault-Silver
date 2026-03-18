# 🤖 Silver AI Employee - Autonomous Task Automation System

> **Version:** 1.0.0 | **Status:** Production Ready ✅ | **Tier:** Silver

A sophisticated AI-powered employee automation system that processes tasks from multiple input channels (Email, WhatsApp, Gmail, File System), analyzes them with Claude AI, and executes actions with full lifecycle tracking.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Components](#components)
- [Usage](#usage)
- [Agent Skills](#agent-skills)
- [MCP Server](#mcp-server)
- [Task Lifecycle](#task-lifecycle)
- [Monitoring & Dashboard](#monitoring--dashboard)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## 🎯 Overview

Silver AI Employee is an autonomous automation system that:

1. **Ingests tasks** from multiple sources (Email, WhatsApp, Gmail, File System)
2. **Analyzes tasks** using Claude AI to generate execution plans
3. **Processes tasks** through a pipeline of classification, prioritization, and execution
4. **Tracks everything** with full lifecycle logging and dashboard metrics
5. **Supports human-in-the-loop** approval workflows for sensitive operations

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 📧 **Email Automation** | Send tracked emails via Gmail SMTP with automatic task creation |
| 📱 **WhatsApp Automation** | Send WhatsApp messages via WhatsApp Web with full tracking |
| 📬 **Gmail Watcher** | Monitor Gmail inbox for new emails, auto-create tasks |
| 📁 **Filesystem Watcher** | Monitor folders for new files, ingest into task pipeline |
| 🤖 **Claude Reasoning** | AI-powered task analysis with Plan.md generation |
| 🛠️ **MCP Server** | Model Context Protocol server with 4 built-in tools |
| ⏰ **Task Scheduler** | Windows Task Scheduler integration for recurring tasks |
| 👤 **Human Approval** | Approval workflows for sensitive operations |
| 📊 **Live Dashboard** | Real-time web dashboard with system metrics |

### Agent Skills (6 Total)

- `classify_task` - Categorizes tasks by type and urgency
- `prioritize_task` - Determines priority using weighted scoring
- `execute_task` - Performs task execution
- `summarize_task` - Generates task summaries
- `update_dashboard` - Updates dashboard metrics
- `human_approval` - Manages approval workflows

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SILVER AI EMPLOYEE FLOW                           │
└─────────────────────────────────────────────────────────────────────────┘

External Inputs                    Processing                    Outputs
───────────────                    ───────────                    ───────

┌─────────────┐
│ Gmail       │────┐
│ (Watcher)   │    │
└─────────────┘    │
                   │      ┌─────────────┐
┌─────────────┐    │      │ Claude      │         ┌─────────────┐
│ Filesystem  │────┼─────▶│ Reasoning   │────────▶│ Plan.md     │
│ (Watcher)   │    │      │ Loop        │         │ (Plans/)    │
└─────────────┘    │      └─────────────┘         └─────────────┘
                   │
┌─────────────┐    │      ┌─────────────┐
│ MCP Server  │────┘      │ Orchestrator│
│ (Tools)     │           │ + Skills    │
└─────────────┘           └──────┬──────┘
                                 │
                          ┌──────┴──────┐
                          │ Human       │
                          │ Approval    │
                          │ (if needed) │
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │ Scheduler   │
                          │ (Recurring) │
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │ Dashboard   │
                          │ (Metrics)   │
                          └─────────────┘
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```bash
# Gmail Configuration
GMAIL_ADDRESS=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Anthropic Claude API (for reasoning loop)
ANTHROPIC_API_KEY=your_claude_api_key

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 3. Start the System

```bash
start_system.bat
```

This starts 6 components in separate windows:
1. **Filesystem Watcher** - Monitors Inbox for new files
2. **Gmail Watcher** - Monitors Gmail for new emails
3. **Claude Reasoning Loop** - Analyzes tasks and creates Plan.md files
4. **Task Scheduler** - Runs scheduled tasks
5. **Orchestrator** - Processes tasks from Needs_Action to Done
6. **Dashboard** - Shows real-time system status

### 4. Test the System

```bash
# Create a test task
echo "Send meeting reminder to team" > Inbox/test_task.md

# Watch it flow: Inbox → Needs_Action → Done
# Check Dashboard.md for updated metrics
```

---

## ⚙️ Configuration

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `GMAIL_ADDRESS` | Your Gmail address | `user@gmail.com` |
| `SMTP_PASSWORD` | Gmail App Password | `xxxx xxxx xxxx xxxx` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `SMTP_SERVER` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |

### Getting Gmail App Password

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and your device
3. Copy the generated 16-character password
4. Add to `.env` file

---

## 🧩 Components

### 1. Filesystem Watcher (`filesystem_watcher.py`)

Monitors the Inbox folder for new files using watchdog.

```bash
python filesystem_watcher.py
```

**Features:**
- Real-time file detection
- Duplicate handling
- Ingestion logging
- Thread-safe operations

---

### 2. Gmail Watcher (`watchers/gmail_watcher.py`)

Monitors Gmail API for new emails.

```bash
python watchers/gmail_watcher.py --interval 60
```

**Features:**
- OAuth2 authentication
- Unread email detection
- Task file creation
- State management

---

### 3. Claude Reasoning Loop (`claude_reasoning.py`)

Uses Claude AI to analyze tasks and generate execution plans.

```bash
# Continuous mode
python claude_reasoning.py --interval 30

# Process once
python claude_reasoning.py --process
```

**Output Example (Plan.md):**
```markdown
# Execution Plan: Plan-20260226-123456-TSK001

## Analysis Summary
| Attribute | Value |
|-----------|-------|
| Category | communication |
| Priority | high |
| Complexity | moderate |

## Execution Steps
| Step | Action | Time |
|------|--------|------|
| 1 | Review message content | 2min |
| 2 | Determine required response | 3min |
| 3 | Execute response action | 5min |
```

---

### 4. Orchestrator (`orchestrator_simple.py`)

Processes tasks from Needs_Action to Done.

```bash
python orchestrator_simple.py
```

**Features:**
- Automatic task classification
- Category detection (email, whatsapp, technical, general)
- State persistence
- Error handling with retry

---

### 5. Task Scheduler (`scheduler.py`)

Manages scheduled and recurring tasks.

```bash
# List scheduled tasks
python scheduler.py list

# Add a task
python scheduler.py add my_task "My Task" "python my_script.py" --schedule interval --interval 10

# Run a task
python scheduler.py run my_task
```

---

### 6. Dashboard (`dashboard_updater.py`, `start_dashboard.py`)

Real-time metrics and web interface.

```bash
# Update metrics
python dashboard_updater.py --action update

# View status
python dashboard_updater.py --action status

# Start web server
python start_dashboard.py
```

---

## 📝 Usage

### Email Command

Send tracked emails:

```bash
email recipient@example.com "Subject" "Message"
```

**Examples:**
```bash
email client@company.com "Meeting Tomorrow" "Our meeting is at 2 PM"
email boss@company.com "Project Update" "Project completed successfully"
```

### WhatsApp Command

Send tracked WhatsApp messages:

```bash
whatsapp +923222208301 "Message" "Project Name"
```

**Examples:**
```bash
whatsapp +923222208301 "Meeting reminder" "Reminders"
whatsapp +919876543210 "Project update" "Updates"
```

### MCP Server Tools

```bash
# Start MCP server with web interface
python mcp_server.py --web

# CLI tool call
python mcp_server.py send_email --params "{\"to\":\"test@example.com\",\"subject\":\"Test\",\"body\":\"Hello\"}"
```

**Available Tools:**
| Tool | Description |
|------|-------------|
| `send_email` | Send email via SMTP |
| `log_activity` | Log activity to system |
| `create_task` | Create new task in Inbox |
| `get_system_status` | Get system metrics |

---

## 🎯 Agent Skills

Located in `skills/` folder:

| Skill | File | Description |
|-------|------|-------------|
| `classify_task` | `classify_task.py` | Categorizes tasks by type and urgency |
| `prioritize_task` | `prioritize_task.py` | Determines priority using weighted scoring |
| `execute_task` | `execute_task.py` | Performs task execution |
| `summarize_task` | `summarize_task.py` | Generates task summaries |
| `update_dashboard` | `update_dashboard.py` | Updates dashboard metrics |
| `human_approval` | `human_approval.py` | Manages approval workflows |

---

## 🔄 Task Lifecycle

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Inbox/    │ ──▶ │ Needs_Action/│ ──▶ │  Plans/     │ ──▶ │  Done/   │
│  (New tasks)│     │ (Processing) │     │ (AI Plans)  │     │(Complete)│
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
       │                    │
       │                    ▼
       │            ┌──────────────┐
       └───────────▶│ Pending_     │
                    │ Approval/    │
                    │ (If needed)  │
                    └──────────────┘
```

---

## 📊 Monitoring & Dashboard

### View System Status

```bash
python dashboard_updater.py --action status
```

### Dashboard Metrics

| Metric | Description |
|--------|-------------|
| Tasks Processed | Total tasks completed |
| Tasks Failed | Failed task count |
| Tasks Pending | Pending tasks |
| Success Rate | Completion percentage |
| Watcher Status | Filesystem/Gmail watcher state |

### Access Web Dashboard

```bash
python start_dashboard.py
# Open: http://localhost:8080/dashboard.html
```

---

## 🛠️ Troubleshooting

### Email not sending?
- Check Gmail App Password in `.env`
- Verify 2FA is enabled on Gmail account
- Regenerate App Password if needed

### WhatsApp not sending?
- Log into [WhatsApp Web](https://web.whatsapp.com)
- Keep browser tab open during automation
- Ensure pyautogui has screen access

### Task stuck in Inbox?
```bash
# Manually run filesystem watcher
python filesystem_watcher.py
```

### Task stuck in Needs_Action?
```bash
# Manually run orchestrator
python orchestrator_simple.py
```

### Claude reasoning not working?
- Check `ANTHROPIC_API_KEY` in `.env`
- Verify API key is valid
- System falls back to rule-based analysis if unavailable

### Dashboard not updating?
```bash
python dashboard_updater.py --action update
```

---

## 📁 Project Structure

```
AI_Employee_vault(Silver)/
├── Inbox/                  # New tasks land here
├── Needs_Action/           # Tasks being processed
├── Done/                   # Completed tasks
├── Pending_Approval/       # Awaiting human approval
├── Plans/                  # Generated execution plans
├── logs/                   # System logs
├── state/                  # Processing state files
├── skills/                 # Agent skills (6 skills)
├── watchers/               # External service watchers
│   └── gmail_watcher.py
├── scheduled_tasks/        # Scheduled task definitions
├── mcp_config/             # MCP server configuration
│
├── start_system.bat        # Start all components
├── start_dashboard.py      # Dashboard web server
├── filesystem_watcher.py   # File ingestion
├── orchestrator_simple.py  # Task processing
├── claude_reasoning.py     # AI analysis
├── scheduler.py            # Task scheduling
├── mcp_server.py           # MCP tools server
├── dashboard_updater.py    # Metrics updater
├── email_send.py           # Email automation
├── whatsapp_auto.py        # WhatsApp automation
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 📄 License

Internal Use - AI Employee Vault Project

---

## 📞 Support

For issues or questions, check the logs in `logs/` folder:
- `orchestration_log.md` - Task processing
- `filesystem_watcher_log.md` - File ingestion
- `claude_reasoning_log.md` - AI analysis
- `mcp_server_log.md` - MCP tool usage
- `scheduler_log.md` - Scheduled tasks

---

*Last Updated: 2026-03-19 | Version: 1.0.0 | Status: ✅ Production Ready*
