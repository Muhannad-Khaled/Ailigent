# Ailigent

**AI-Powered HR & Operations Suite for Odoo**

Ailigent is a comprehensive suite of 5 AI-powered microservices that integrate seamlessly with Odoo ERP to transform HR operations through intelligent automation.

## Overview

| Service | Port | Description |
|---------|------|-------------|
| **Employee Agent** | 8000 | Telegram bot for employee self-service |
| **Contracts Agent** | 8001 | Contract lifecycle management |
| **HR Agent** | 8002 | Recruitment, appraisals, attendance analytics |
| **Task Management** | 8003 | Task distribution & workload optimization |
| **Voice Agent** | 8004 | Voice-based AI assistant using LiveKit |

## Features

### Employee Self-Service (Telegram Bot)
- Natural language queries in English & Arabic
- Leave balance inquiries
- Payslip viewing
- Task management
- AI-generated daily summaries
- Secure OTP-based account linking

### HR Management
- **Recruitment**: CV upload, AI-powered analysis & scoring, candidate ranking
- **Attendance**: Anomaly detection, leave approvals, department reports
- **Appraisals**: Performance tracking, AI feedback summarization
- **Reports**: Headcount, turnover, AI-generated HR insights

### Contract Management
- Contract lifecycle tracking
- AI-powered clause extraction
- Risk assessment & compliance monitoring
- Expiry alerts & milestone tracking
- Integration with Odoo documents

### Task Management
- AI-optimized task distribution
- Workload balancing across teams
- Bottleneck detection
- Overdue task monitoring
- Performance reports

### Voice AI Assistant
- Real-time voice interaction via LiveKit
- Bilingual support (English/Arabic)
- Hands-free HR queries
- Integration with all backend services

## Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **AI**: Google Gemini API
- **ERP**: Odoo 18 (XML-RPC)
- **Voice**: LiveKit
- **Messaging**: Telegram Bot API
- **Scheduler**: APScheduler

## Quick Start

### Prerequisites
- Python 3.10+
- Odoo 18 instance with HR modules
- Google Gemini API key
- Telegram Bot Token (for employee-agent)
- LiveKit credentials (for voice-agent)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Muhannad-Khaled/Ailigent.git
   cd Ailigent
   ```

2. **Create virtual environments for each service**
   ```bash
   # Employee Agent
   cd employee-agent
   python -m venv employeeEnv
   employeeEnv\Scripts\activate  # Windows
   pip install -r requirements.txt

   # Repeat for other services...
   ```

3. **Configure environment variables**
   ```bash
   # Copy the template
   cp .env.example .env

   # Edit .env with your configuration
   ```

4. **Start the services**
   ```bash
   # Terminal 1 - Employee Agent
   cd employee-agent
   uvicorn app.main:app --port 8000

   # Terminal 2 - Contracts Agent
   cd contracts-agent
   uvicorn app.main:app --port 8001

   # Terminal 3 - HR Agent
   cd hr-agent
   uvicorn app.main:app --port 8002

   # Terminal 4 - Task Management
   cd task-management
   uvicorn app.main:app --port 8003

   # Terminal 5 - Voice Agent
   cd voice-agent
   uvicorn app.main:app --port 8004
   ```

## Configuration

### Environment Variables

Create a `.env` file in each service directory or use the root `.env` file:

```env
# Odoo Configuration
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USER=your_username
ODOO_PASSWORD=your_password

# API Keys
API_KEY=your-secure-api-key
GEMINI_API_KEY=your-gemini-api-key

# Telegram (employee-agent only)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# LiveKit (voice-agent only)
LIVEKIT_URL=wss://your-livekit-server
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### API Keys by Service

| Service | API Key |
|---------|---------|
| Employee Agent | `ailigent-employee-api-key-2024` |
| Contracts Agent | `ailigent-contracts-api-key-2024` |
| HR Agent | `ailigent-hr-api-key-2024` |
| Task Management | `ailigent-task-api-key-2024` |

## API Documentation

Each service provides Swagger UI documentation:

- Employee Agent: http://localhost:8000/docs
- Contracts Agent: http://localhost:8001/docs
- HR Agent: http://localhost:8002/docs
- Task Management: http://localhost:8003/docs
- Voice Agent: http://localhost:8004/docs

### Key Endpoints

#### HR Agent (Port 8002)
```
POST /api/v1/recruitment/applicants/upload    # Upload CV
POST /api/v1/recruitment/applicants/{id}/analyze  # AI analysis
GET  /api/v1/attendance/leave/pending         # Pending leaves
POST /api/v1/attendance/leave/{id}/approve    # Approve leave
GET  /api/v1/attendance/anomalies             # Detect anomalies
POST /api/v1/reports/insights                 # AI HR insights
```

#### Contracts Agent (Port 8001)
```
GET  /api/v1/contracts                        # List contracts
POST /api/v1/contracts/{id}/analyze           # AI analysis
GET  /api/v1/contracts/expiring?days=30       # Expiring soon
GET  /api/v1/compliance/score/{id}            # Compliance score
```

#### Task Management (Port 8003)
```
GET  /api/v1/tasks                            # List tasks
POST /api/v1/distribution/recommend/{task_id} # AI assignment
GET  /api/v1/distribution/bottlenecks         # Find bottlenecks
GET  /api/v1/employees/workload               # Team workload
```

### Authentication

All API endpoints (except /health) require an API key:

```bash
curl -X GET "http://localhost:8002/api/v1/attendance/summary" \
  -H "X-API-Key: ailigent-hr-api-key-2024"
```

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/link` | Link Telegram to employee account |
| `/leave` | Check leave balance |
| `/payslip` | View latest payslip |
| `/tasks` | View assigned tasks |
| `/summary` | AI-generated daily summary |
| `/help` | List available commands |

## Project Structure

```
Ailigent/
├── employee-agent/          # Telegram bot service
│   ├── app/
│   │   ├── handlers/        # Bot command handlers
│   │   ├── services/        # Odoo, Gemini, Email services
│   │   └── main.py
│   └── requirements.txt
│
├── contracts-agent/         # Contract management service
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── services/        # AI, Odoo services
│   │   └── scheduler/       # Background jobs
│   └── requirements.txt
│
├── hr-agent/                # HR management service
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── services/        # AI, Odoo, Document services
│   │   └── scheduler/       # Background jobs
│   └── requirements.txt
│
├── task-management/         # Task distribution service
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── services/        # AI optimization services
│   │   └── scheduler/       # Background jobs
│   └── requirements.txt
│
├── voice-agent/             # Voice AI service
│   ├── app/
│   │   ├── agent/           # LiveKit voice agent
│   │   └── services/        # Backend integrations
│   └── requirements.txt
│
├── .env.example             # Environment template
├── .gitignore
└── README.md
```

## Odoo Integration

### Required Odoo Modules
- `hr` - Core HR
- `hr_recruitment` - Recruitment
- `hr_holidays` - Leave management
- `hr_attendance` - Attendance tracking
- `project` - Project & Task management

### Supported Odoo Models
- `hr.employee` - Employee records
- `hr.department` - Departments
- `hr.job` - Job positions
- `hr.applicant` - Job applicants
- `hr.leave` - Leave requests
- `hr.attendance` - Attendance records
- `project.task` - Tasks
- `ir.attachment` - Documents

## Development

### Running Tests
```bash
cd hr-agent
pytest tests/
```

### Docker Support
Each service includes Docker configuration:
```bash
cd hr-agent/docker
docker-compose up -d
```

## Security

- API key authentication on all endpoints
- OTP verification for Telegram account linking
- HMAC-signed webhooks for notifications
- Environment variables for sensitive data
- CORS configuration for web access

## License

This project is proprietary software.

## Support

For issues and feature requests, please open an issue on GitHub.

---

**Ailigent Suite** - Intelligent Workforce Management for Odoo
