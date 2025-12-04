# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HR Agent is an AI-powered HR automation microservice that integrates with Odoo ERP. It's part of the Ailigent suite alongside:
- **employee-agent**: Telegram bot for employee self-service
- **task-management**: Task distribution and workload optimization
- **contracts-agent**: Contract lifecycle management

All services share a common Odoo backend and Google Gemini AI integration.

## Commands

### Run Development Server
```bash
uvicorn app.main:app --reload --port 8002
```

### Run with Docker
```bash
cd docker
docker-compose up -d
```

### Run Tests
```bash
pytest
pytest tests/test_api/  # specific directory
pytest -k "test_name"   # single test
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Service Layer Pattern
The application uses a service layer pattern with singleton instances:

- **OdooClient** (`app/services/odoo/client.py`): Singleton XML-RPC client with module availability checking
- **GeminiClient** (`app/services/ai/gemini_client.py`): Singleton for Google Gemini API with HR-specific methods
- **TaskManagementService** (`app/services/integration/task_service.py`): Integration with task-management service

### Odoo Integration
All Odoo operations go through service classes:
- `RecruitmentService`: hr.job, hr.applicant, hr.recruitment.stage, calendar.event
- `AppraisalService`: hr.appraisal, hr.appraisal.goal
- `EmployeeService`: hr.employee, hr.department (for reports)
- `AttendanceService`: hr.attendance, hr.leave, hr.leave.allocation

**Module Flexibility**: The OdooClient checks which modules are installed and gracefully degrades if recruitment or appraisal modules are missing.

### AI Services
AI features are in `app/services/ai/`:
- `cv_analyzer`: CV parsing and scoring against job requirements
- `feedback_summarizer`: Appraisal feedback summarization
- `report_generator`: HR insights generation
- `prompts.py`: All LLM prompt templates

### Document Processing
- `cv_parser.py`: Extract text from PDF (PyPDF2) and DOCX (python-docx)
- `report_exporter.py`: Generate PDF (reportlab) and Excel (openpyxl) reports

### Scheduler
APScheduler runs background jobs in `app/scheduler/jobs/`:
- `appraisal_reminder.py`: Daily appraisal deadline reminders
- `interview_reminder.py`: Interview reminders (every N hours)
- `attendance_anomaly.py`: Daily attendance anomaly detection
- `report_scheduler.py`: Weekly HR report generation

### API Structure
All endpoints under `/api/v1/` with API key authentication via `X-API-Key` header.

Router modules in `app/api/v1/`:
- `health.py`: Health checks (public)
- `recruitment.py`: CV upload, applicant management, interview scheduling
- `appraisals.py`: Performance review tracking, AI summarization
- `reports.py`: Headcount, turnover, department metrics
- `attendance.py`: Leave approvals, anomaly detection

### Configuration
Settings loaded from environment via pydantic-settings in `app/config.py`.
Copy `.env.example` to `.env` for local development.

**Required**:
- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
- `API_KEY`

**Optional**:
- `GEMINI_API_KEY` (AI features)
- `REDIS_URL` (caching)
- `SMTP_*` (email notifications)
- `TASK_MANAGEMENT_URL`, `TASK_MANAGEMENT_API_KEY` (integration)

## Key Patterns

### Graceful Module Handling
```python
def _ensure_recruitment_module(self):
    if not self.client.is_model_available(ODOO_MODEL_APPLICANT):
        raise OdooModuleNotFoundError(...)
```

### AI with Fallback
```python
if gemini.is_available():
    analysis = await gemini.analyze_cv(...)
else:
    # Use basic rule-based analysis
    analysis = basic_analyze(...)
```

### Integration with Task Management
```python
from app.services.integration.task_service import get_task_management_service

service = get_task_management_service()
await service.create_onboarding_tasks(employee_id, employee_name, manager_id, department)
```

## API Examples

### Upload CV
```bash
curl -X POST "http://localhost:8002/api/v1/recruitment/applicants/upload" \
  -H "X-API-Key: your-key" \
  -F "job_id=1" \
  -F "applicant_name=John Doe" \
  -F "email=john@example.com" \
  -F "cv_file=@resume.pdf"
```

### Analyze CV with AI
```bash
curl -X POST "http://localhost:8002/api/v1/recruitment/applicants/1/analyze" \
  -H "X-API-Key: your-key"
```

### Get Pending Appraisals
```bash
curl "http://localhost:8002/api/v1/appraisals/pending?days_until_deadline=7" \
  -H "X-API-Key: your-key"
```

### Generate HR Insights
```bash
curl -X POST "http://localhost:8002/api/v1/reports/insights" \
  -H "X-API-Key: your-key"
```

### Approve Leave
```bash
curl -X POST "http://localhost:8002/api/v1/attendance/leave/1/approve" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Approved"}'
```

## Port Configuration
- **HR Agent**: 8002 (this service)
- **Task Management**: 8000
- **Contracts Agent**: 8001
- **Employee Agent**: 8000 (runs separately)

## Docker Networks
When running with Docker, use `ailigent-network` for cross-service communication:
```yaml
networks:
  ailigent-network:
    external: true
```
