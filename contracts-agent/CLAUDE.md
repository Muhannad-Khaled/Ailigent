# Contracts Agent

AI-powered Contract Lifecycle Management system integrated with Odoo ERP.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your configuration

# Run the server
python -m app.main
# Or with uvicorn
uvicorn app.main:app --reload --port 8001
```

## Project Structure

```
contracts-agent/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment configuration
│   ├── api/                    # REST API endpoints
│   │   ├── v1/                 # API version 1
│   │   │   ├── contracts.py    # Contract CRUD
│   │   │   ├── clauses.py      # Clause extraction
│   │   │   ├── milestones.py   # Milestone tracking
│   │   │   ├── compliance.py   # Compliance monitoring
│   │   │   └── reports.py      # Report generation
│   │   └── middleware/         # Auth and logging
│   ├── models/                 # Pydantic data models
│   ├── services/               # Business logic
│   │   ├── odoo/               # Odoo integration
│   │   ├── ai/                 # Gemini AI services
│   │   └── notifications/      # Webhook notifications
│   └── scheduler/              # Background jobs
└── requirements.txt
```

## Key Features

- **Contract Management**: CRUD operations linked to Odoo documents
- **AI Analysis**: Clause extraction and risk assessment using Gemini
- **Milestone Tracking**: Delivery date monitoring with alerts
- **Compliance Monitoring**: Track requirements and calculate scores
- **Expiry Alerts**: Automated notifications for expiring contracts
- **Reports**: Portfolio, expiry, compliance, and risk reports

## API Endpoints

- `GET /api/v1/contracts` - List contracts
- `POST /api/v1/contracts` - Create contract
- `GET /api/v1/contracts/{id}` - Get contract details
- `POST /api/v1/contracts/{id}/analyze` - AI analysis
- `POST /api/v1/clauses/extract/{contract_id}` - Extract clauses
- `GET /api/v1/milestones/upcoming` - Upcoming milestones
- `GET /api/v1/compliance/score/{contract_id}` - Compliance score
- `GET /api/v1/reports/portfolio` - Portfolio report
- `GET /api/v1/health` - Health check

## Configuration

Required environment variables:
- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` - Odoo connection
- `GEMINI_API_KEY` - Google Gemini API key
- `API_KEY` - API authentication key
- `WEBHOOK_*` - Webhook URLs for notifications

## Architecture Notes

- Follows patterns from sibling projects (employee-agent, task-management)
- Uses Odoo `ir.attachment` for document storage
- In-memory storage for contract metadata (can be extended to database)
- Singleton pattern for Odoo and Gemini clients
- APScheduler for background monitoring jobs
