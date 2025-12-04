# CLAUDE.md

This file provides guidance to Claude Code when working with the voice-agent project.

## Project Overview

Voice Agent is a LiveKit-powered voice AI assistant that integrates with the Ailigent suite:
- **employee-agent** (port 8000): Telegram bot for employee self-service
- **task-management** (port 8003): Task distribution and workload optimization
- **contracts-agent** (port 8001): Contract lifecycle management
- **hr-agent** (port 8002): HR automation

The voice agent provides a voice interface to interact with all these services via LiveKit Cloud.

## Quick Start

### 1. Install Dependencies
```bash
cd E:\Ailigent\voice-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
The `.env` file is already configured with:
- LiveKit Cloud credentials
- Odoo connection details
- Google API key for Gemini
- Service URLs and API keys

### 3. Run the Voice Agent

**Option A: Run as LiveKit Agent Worker (for voice)**
```bash
python -m livekit.agents dev app.agent.voice_agent:entrypoint
```

**Option B: Run FastAPI Server (for REST API)**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8004
```

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  Web/Mobile     │────▶│   LiveKit Cloud     │────▶│   voice-agent   │
│  Voice Client   │     │   (WebRTC)          │     │   (Port 8004)   │
└─────────────────┘     └─────────────────────┘     └────────┬────────┘
                                                             │
              ┌──────────────────────────────────────────────┼──────┐
              │                      │                       │      │
              ▼                      ▼                       ▼      ▼
     ┌────────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────┐
     │ employee-agent │    │ task-mgmt   │    │ hr-agent     │    │Odoo │
     │ (8000)         │    │ (8003)      │    │ (8002)       │    │ ERP │
     └────────────────┘    └─────────────┘    └──────────────┘    └─────┘
```

## Project Structure

```
voice-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI + entry point
│   ├── config.py            # Pydantic settings
│   ├── agent/
│   │   ├── __init__.py
│   │   └── voice_agent.py   # LiveKit agent with 15+ tools
│   ├── services/
│   │   ├── __init__.py
│   │   ├── odoo_service.py  # Direct Odoo XML-RPC
│   │   └── http_clients.py  # HTTP clients for other services
│   └── utils/
│       ├── __init__.py
│       ├── language.py      # Arabic/English detection
│       └── prompts.py       # System prompts
├── requirements.txt
├── .env
└── CLAUDE.md
```

## Voice Tools

### Employee Self-Service
- `get_all_employees` - List all employees
- `get_employee_info` - Get employee details by ID
- `get_leave_balance` - Check leave balance
- `get_leave_requests` - View leave requests
- `get_payslips` - View recent payslips
- `get_attendance` - View attendance summary
- `get_employee_tasks` - View assigned tasks

### Task Management
- `get_all_tasks` - Get all team tasks
- `get_overdue_tasks` - Get overdue tasks
- `get_workload_analysis` - Team workload analysis

### HR Management (Managers)
- `get_pending_leave_approvals` - Pending leave requests
- `get_hr_headcount_report` - Headcount report
- `get_hr_insights` - AI-powered HR insights

### Contract Management
- `get_expiring_contracts` - Contracts expiring soon
- `get_contract_compliance_report` - Compliance status

### Utility
- `switch_language` - Switch between English/Arabic

## Configuration

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit Cloud WebSocket URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `ODOO_URL` | Odoo server URL |
| `ODOO_DB` | Odoo database name |
| `ODOO_USERNAME` | Odoo API username |
| `ODOO_PASSWORD` | Odoo API password |

## Key Files

| File | Purpose |
|------|---------|
| `app/agent/voice_agent.py` | Main agent with function tools |
| `app/services/odoo_service.py` | Odoo XML-RPC operations |
| `app/services/http_clients.py` | HTTP clients for backend services |
| `app/utils/prompts.py` | System prompts in English/Arabic |

## Technology Stack

- **LiveKit Agents SDK** - Real-time voice AI framework
- **Google Gemini** - LLM for conversation and function calling
- **Google STT/TTS** - Speech recognition and synthesis
- **Silero VAD** - Voice activity detection
- **FastAPI** - REST API for health checks
- **Odoo XML-RPC** - ERP integration

## Bilingual Support

The agent auto-detects language based on user speech:
- English: Uses Gemini voices (Puck)
- Arabic: Uses Google TTS with Arabic voice
- Users can say "switch to Arabic" or "التبديل للإنجليزية"
