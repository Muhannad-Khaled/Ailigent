# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Task Management Agent is an AI-powered external Python service that integrates with Odoo 17+ via XML-RPC for task distribution and tracking. It uses Google Gemini for intelligent features like workload optimization and bottleneck detection.

## Commands

### Run Development Server
```bash
uvicorn app.main:app --reload
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
The application uses a service layer pattern with singleton instances for external connections:

- **OdooClient** (`app/services/odoo/client.py`): Singleton XML-RPC client that wraps all Odoo operations. Use `get_odoo_client()` to access.
- **GeminiClient** (`app/services/ai/gemini_client.py`): Singleton wrapper for Google Gemini API. Gracefully degrades if API key not configured.
- **RedisClient** (`app/services/cache/redis_client.py`): Async Redis client for caching.

### Odoo Integration
All Odoo operations go through service classes that use the OdooClient:
- `OdooTaskService`: Operations on `project.task` model
- `OdooEmployeeService`: Operations on `hr.employee` and `res.users` models

Key Odoo models: `project.task`, `project.project`, `project.task.type`, `res.users`, `hr.employee`

### AI Services
AI features have fallback basic implementations when Gemini is unavailable:
- `WorkloadOptimizer`: Analyzes team workload, recommends task assignments
- `BottleneckDetector`: Identifies workflow bottlenecks in stages and employees
- `AIReportGenerator`: Creates productivity reports with AI insights

Prompts are centralized in `app/services/ai/prompts.py`.

### Scheduler
APScheduler runs background jobs defined in `app/scheduler/jobs/`:
- `overdue_monitor.py`: Checks overdue tasks every 15 minutes
- `report_generator.py`: Daily (6 AM) and weekly (Monday 7 AM) reports
- `workload_balancer.py`: Hourly workload distribution checks

### Notification System
`NotificationManager` orchestrates both channels:
- `EmailService`: Async SMTP with HTML templates
- `WebhookService`: HMAC-signed payloads with retry logic

### API Structure
All endpoints under `/api/v1/` with API key authentication via `X-API-Key` header. Health endpoints at `/api/v1/health/*` are public.

Router modules in `app/api/v1/`:
- `tasks.py`: Task CRUD and workload queries
- `employees.py`: Employee listings and workload details
- `distribution.py`: AI-powered assignment recommendations
- `reports.py`: Productivity metrics and reports

### Configuration
Settings loaded from environment via pydantic-settings in `app/config.py`. Copy `.env.example` to `.env` for local development.

Required: `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`, `API_KEY`
Optional: `GEMINI_API_KEY` (AI features), `SMTP_*` (email), `WEBHOOK_*` (webhooks)
