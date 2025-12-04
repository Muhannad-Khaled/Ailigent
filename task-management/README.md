# Task Management Agent

AI-powered task distribution and tracking system integrated with Odoo 17+.

## Features

- **Task Management**: List, update, and assign tasks via Odoo integration
- **Smart Distribution**: AI-powered task assignment recommendations using Google Gemini
- **Workload Analysis**: Monitor employee workload and utilization
- **Bottleneck Detection**: AI identifies workflow bottlenecks and suggests improvements
- **Productivity Reports**: Daily/weekly AI-enhanced reports with insights
- **Automatic Alerts**: Email and webhook notifications for overdue tasks
- **Scheduled Jobs**: Automated monitoring and report generation

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Odoo Integration**: XML-RPC (Odoo 17+)
- **AI/LLM**: Google Gemini (gemini-2.0-flash)
- **Cache/Queue**: Redis
- **Scheduler**: APScheduler
- **Notifications**: Email (SMTP) + Webhooks

## Quick Start

### Prerequisites

- Python 3.11+
- Redis
- Odoo 17+ instance
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
cd task-management
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

### Docker Deployment

```bash
cd docker
docker-compose up -d
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
# Odoo Connection
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_db
ODOO_USER=admin
ODOO_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379/0

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# API Authentication
API_KEY=your_secure_api_key

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_app_password

# Webhooks (Optional)
WEBHOOK_SECRET=your_secret
WEBHOOK_OVERDUE_URL=https://your-webhook.com/overdue
```

## API Endpoints

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/odoo` - Odoo connection status
- `GET /api/v1/health/redis` - Redis connection status

### Tasks
- `GET /api/v1/tasks` - List tasks
- `GET /api/v1/tasks/{id}` - Get task details
- `GET /api/v1/tasks/overdue` - Get overdue tasks
- `GET /api/v1/tasks/workload/{user_id}` - Get employee workload
- `POST /api/v1/tasks/{id}/assign` - Assign task

### Employees
- `GET /api/v1/employees` - List employees
- `GET /api/v1/employees/{id}/workload` - Get employee workload details
- `GET /api/v1/employees/workload-summary` - Team workload summary
- `GET /api/v1/employees/available` - Get available assignees

### AI Distribution
- `POST /api/v1/distribution/recommend/{task_id}` - Get AI assignment recommendation
- `POST /api/v1/distribution/auto-assign/{task_id}` - Auto-assign using AI
- `GET /api/v1/distribution/balance` - Workload balance analysis
- `GET /api/v1/distribution/bottlenecks` - Bottleneck analysis

### Reports
- `GET /api/v1/reports/productivity` - Productivity metrics
- `GET /api/v1/reports/stages` - Stage distribution report
- `GET /api/v1/reports/workload` - Workload report
- `POST /api/v1/reports/generate` - Generate custom report

## Scheduled Jobs

| Job | Frequency | Description |
|-----|-----------|-------------|
| Overdue Monitor | Every 15 min | Check & alert overdue tasks |
| Daily Report | 6:00 AM | Generate daily productivity report |
| Weekly Report | Monday 7:00 AM | Generate weekly summary |
| Workload Balance | Every hour | Check workload distribution |

## Authentication

All endpoints (except `/health`) require an API key via `X-API-Key` header:

```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/v1/tasks
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
