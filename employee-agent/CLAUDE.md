# CLAUDE.md - Ailigent Employee Agent

> AI assistant context file for the Ailigent employee-agent project.

## Project Overview

**Ailigent** is an AI-powered Telegram bot that serves as an intelligent employee self-service assistant. It integrates:

- **Telegram Bot** - User interface for employees
- **Odoo ERP** - HR data source (leave, payslips, attendance, tasks)
- **Google Gemini AI** - Natural language understanding with automatic function calling
- **MCP (Model Context Protocol)** - Standardized AI tool integration

### Key Capabilities

- Check leave balance and request time off
- View payslips and salary information
- Track attendance records
- Manage tasks and projects
- Access company policies
- Get AI-powered daily work summaries
- Bilingual support (English & Arabic)

---

## Quick Start (End Users)

### 1. Find the Bot
Search for your company's Ailigent bot on Telegram (bot name configured by admin).

### 2. Link Your Account
```
1. Send /link to the bot
2. Enter your work email address
3. Check your email for a 6-digit verification code
4. Enter the code in Telegram
5. You're connected!
```

### 3. Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show all commands |
| `/link` | Link Telegram to your employee account |
| `/unlink` | Unlink your account |
| `/leave` | View leave balance and requests |
| `/payslip` | View recent payslips |
| `/attendance` | View attendance summary |
| `/tasks` | View your tasks |
| `/summary` | Get AI-generated daily work summary |
| `/policy` | Search company policies |
| `/cancel` | Cancel current operation |

### 4. Natural Conversation
Just type your question! The AI understands natural language:
- "What's my leave balance?"
- "Show me my last payslip"
- "كم رصيد إجازاتي؟" (Arabic supported)

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Telegram User  │────▶│  Telegram Bot    │────▶│  Bot Handlers   │
└─────────────────┘     │  (polling)       │     │                 │
                        └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────────────────────┼─────────────────┐
                        │                                 │                 │
                        ▼                                 ▼                 ▼
              ┌─────────────────┐              ┌─────────────────┐  ┌──────────────┐
              │  Gemini Service │◀────────────▶│  Odoo Service   │  │  MCP Server  │
              │  (AI + Tools)   │              │  (XML-RPC)      │  │  (FastMCP)   │
              └─────────────────┘              └────────┬────────┘  └──────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   Odoo ERP      │
                                              │   (hr, payroll) │
                                              └─────────────────┘
```

### Request Flow (AI Conversation)

1. User sends message to Telegram bot
2. Bot checks if user is linked (via Odoo ir.config_parameter)
3. Message sent to GeminiService with employee context
4. Gemini analyzes message, decides which tools to call
5. GeminiService executes tool calls via OdooService
6. Results sent back to Gemini
7. Gemini generates natural language response
8. Response sent to user on Telegram

---

## Project Structure

```
employee-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point, lifespan management
│   ├── config.py               # Pydantic settings from .env
│   │
│   ├── handlers/
│   │   ├── __init__.py         # setup_handlers() export
│   │   └── bot_handlers.py     # All Telegram commands & message handling
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── employee.py         # Pydantic data models
│   │
│   ├── services/
│   │   ├── __init__.py         # Service exports
│   │   ├── odoo_service.py     # Odoo XML-RPC integration
│   │   ├── gemini_service.py   # Google Gemini AI + MCP tools
│   │   └── email_service.py    # OTP email sending via Odoo
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── odoo_mcp_server.py  # MCP server with tools & resources
│   │
│   └── utils/
│       ├── __init__.py
│       └── otp.py              # OTP generation & verification
│
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
└── CLAUDE.md                   # This file
```

---

## Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| **Web Framework** | FastAPI | >=0.109.0 |
| **ASGI Server** | Uvicorn | >=0.27.0 |
| **Telegram Bot** | python-telegram-bot | >=21.0 |
| **AI/LLM** | google-generativeai (Gemini 1.5 Flash) | >=0.8.0 |
| **MCP SDK** | mcp (FastMCP) | >=1.0.0 |
| **ERP Integration** | Odoo (XML-RPC) | Built-in xmlrpc.client |
| **Data Validation** | Pydantic | >=2.5.0 |
| **Settings** | pydantic-settings | >=2.1.0 |
| **Environment** | python-dotenv | >=1.0.0 |
| **Logging** | loguru | >=0.7.2 |
| **Async HTTP** | aiohttp | >=3.9.0 |

---

## Key Components

### 1. FastAPI Application (`app/main.py`)

Entry point with async lifespan management:

```python
# Routes
GET /           # Status endpoint
GET /health     # Service health check
GET /mcp/tools  # List available MCP tools

# Lifespan Events
- Startup: Initialize Odoo → MCP → Gemini → Telegram bot
- Shutdown: Stop Telegram polling, cleanup
```

### 2. Bot Handlers (`app/handlers/bot_handlers.py`)

- **Command Handlers**: /start, /help, /link, /unlink, /leave, /payslip, /attendance, /tasks, /summary, /policy, /cancel
- **Conversation Handler**: Account linking flow (email → OTP verification)
- **Message Handler**: AI-powered free-form conversation
- **Bilingual Messages**: MESSAGES dict with 'en' and 'ar' translations
- **Language Detection**: Auto-detects Arabic via Unicode range (\u0600-\u06FF)

### 3. Odoo Service (`app/services/odoo_service.py`)

XML-RPC client for Odoo ERP:

| Method | Description |
|--------|-------------|
| `connect()` | Authenticate with Odoo |
| `find_employee_by_email()` | Look up employee by work email |
| `get_employee_by_id()` | Get employee details |
| `get_leave_balance()` | Get all leave type balances |
| `get_leave_requests()` | Get leave requests (optionally by state) |
| `create_leave_request()` | Submit new leave request |
| `get_payslips()` | Get recent payslips |
| `get_attendance_summary()` | Get monthly attendance stats |
| `get_employee_tasks()` | Get assigned tasks |
| `create_task()` | Create new task |
| `get_company_policies()` | List company policies |
| `save_telegram_link()` | Store Telegram↔Employee mapping |
| `get_employee_by_telegram()` | Look up employee by Telegram ID |
| `remove_telegram_link()` | Delete Telegram mapping |

**Telegram Link Storage**: Uses Odoo's `ir.config_parameter` model with key format `telegram_link_{telegram_id}` = `{employee_id}|{username}`

### 4. Gemini Service (`app/services/gemini_service.py`)

AI service with MCP-style function calling:

- **Model**: Gemini 1.5 Flash
- **Tools**: 8 function declarations for Odoo operations
- **Chat Sessions**: Per-user conversation history
- **Function Calling**: Iterative tool execution (max 5 iterations)
- **Language Detection**: Arabic vs English based on character ratio

**Available AI Tools**:
- `get_employee_info` - Employee details
- `get_leave_balance` - Leave balances
- `get_leave_requests` - Leave request history
- `get_payslips` - Payslip summaries
- `get_attendance_summary` - Monthly attendance
- `get_employee_tasks` - Task list
- `create_task` - New task creation
- `get_company_policies` - Policy list

### 5. MCP Server (`app/mcp/odoo_mcp_server.py`)

FastMCP server for standardized AI tool access:

**Tools**: Mirrors Gemini tools + Telegram linking operations
**Resources**:
- `employee://{employee_id}/summary` - Complete employee overview
- `policies://list` - All company policies

**Prompts**:
- `daily_summary_prompt` - Generate work summary
- `leave_request_prompt` - Process leave request

### 6. OTP Manager (`app/utils/otp.py`)

- Generates 6-digit OTPs
- Session storage with 10-minute expiry
- Maximum 3 verification attempts
- Secure comparison via `secrets.compare_digest`

---

## Configuration

### Environment Variables

Create `.env` from `.env.example`:

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `GOOGLE_API_KEY` | Yes | Google AI Studio API key |
| `ODOO_URL` | Yes | Odoo instance URL (https://...) |
| `ODOO_DB` | Yes | Odoo database name |
| `ODOO_USERNAME` | Yes | Odoo API user email |
| `ODOO_PASSWORD` | Yes | Odoo API user password |
| `ENVIRONMENT` | No | `development` or `production` (default: development) |
| `DEBUG` | No | Enable debug mode (default: true) |
| `API_HOST` | No | API bind address (default: 0.0.0.0) |
| `API_PORT` | No | API port (default: 8000) |

### Odoo Requirements

- `hr` module (employees)
- `hr_holidays` module (leave management)
- `hr_payroll` module (payslips)
- `hr_attendance` module (attendance)
- `project` module (tasks) - optional
- SMTP configured for OTP emails

---

## Development Guide

### Setup

```bash
# Clone and enter directory
cd employee-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your credentials
```

### Running

```bash
# Development (with auto-reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or directly
python app/main.py
```

### Verification

1. Check startup logs for:
   - "Connected to Odoo"
   - "Initialized Gemini AI with MCP tools"
   - "Telegram bot started"

2. Test endpoints:
   - `GET http://localhost:8000/` - Status
   - `GET http://localhost:8000/health` - Health check
   - `GET http://localhost:8000/mcp/tools` - Tool list

3. Test bot:
   - Send `/start` to your bot on Telegram
   - Try `/link` to test account linking

### Common Issues

| Issue | Solution |
|-------|----------|
| "Odoo connection failed" | Check ODOO_URL, credentials, and network access |
| "Employee not found" | Verify work_email field in Odoo hr.employee |
| OTP email not received | Check Odoo SMTP configuration and mail logs |
| Arabic not detected | Ensure message contains >30% Arabic characters |
| Function calling loops | Check max_iterations in process_message() |

### Key Files to Modify

| Task | File(s) |
|------|---------|
| Add new bot command | `app/handlers/bot_handlers.py` |
| Add new Odoo query | `app/services/odoo_service.py` |
| Add new AI tool | `app/services/gemini_service.py` (ODOO_TOOLS) |
| Add new MCP tool | `app/mcp/odoo_mcp_server.py` |
| Change AI behavior | `_get_system_prompt()` in gemini_service.py |
| Add translations | MESSAGES dict in bot_handlers.py |

---

## API Reference

### REST Endpoints

```
GET /
Response: { "name": "...", "status": "running", "version": "1.0.0" }

GET /health
Response: { "status": "healthy", "odoo_connected": true, "telegram_running": true, "mcp_enabled": true }

GET /mcp/tools
Response: { "server": "...", "tools": [...], "resources": [...] }
```

### MCP Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `get_employee_info` | employee_id (int) | Get employee details |
| `find_employee_by_email` | email (str) | Find employee by email |
| `get_leave_balance` | employee_id (int) | Get all leave balances |
| `get_leave_requests` | employee_id, state? | Get leave requests |
| `create_leave_request` | employee_id, leave_type_id, date_from, date_to, reason? | Create leave request |
| `get_payslips` | employee_id, limit? | Get payslips |
| `get_attendance_summary` | employee_id, month?, year? | Get attendance |
| `get_employee_tasks` | employee_id | Get tasks |
| `create_task` | employee_id, name, description?, due_date? | Create task |
| `get_company_policies` | - | Get policies |
| `check_telegram_link` | telegram_id | Check if linked |
| `link_telegram_account` | telegram_id, employee_id, username? | Link accounts |
| `unlink_telegram_account` | telegram_id | Unlink accounts |

### MCP Resources

| URI | Description |
|-----|-------------|
| `employee://{employee_id}/summary` | Complete employee status |
| `policies://list` | All company policies |

---

## Data Models

Located in `app/models/employee.py`:

- `Employee` - Employee profile data
- `EmployeeLink` - Telegram↔Odoo mapping
- `LeaveBalance` - Leave type balance
- `LeaveRequest` - Leave request details
- `PayslipSummary` - Payslip summary
- `Task` - Task details
- `VerificationSession` - OTP session
- `ConversationContext` - AI conversation state

---

## Security Notes

- OTP sessions expire after 10 minutes
- Maximum 3 OTP verification attempts
- Telegram links stored in Odoo (not local DB)
- Employee ID injected automatically (users can't access others' data)
- Gemini safety filters set to BLOCK_NONE (internal use assumption)
