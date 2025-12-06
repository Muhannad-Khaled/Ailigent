"""Task API Controller - Proxy to FastAPI backend."""

import logging
from odoo import http
from odoo.http import request
import requests as http_requests

_logger = logging.getLogger(__name__)


class TaskAPIController(http.Controller):
    """Controller to proxy requests to the Task Management FastAPI service."""

    def _get_api_settings(self):
        """Get API settings."""
        return request.env['ailigent.task.settings'].sudo().get_settings()

    def _make_api_request(self, method, endpoint, data=None, timeout=60):
        """Make request to FastAPI backend."""
        settings = self._get_api_settings()
        if not settings.api_url:
            return {'error': 'API URL not configured'}

        url = f"{settings.api_url.rstrip('/')}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if settings.api_key:
            headers['X-API-Key'] = settings.api_key

        try:
            if method == 'GET':
                response = http_requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = http_requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return {'error': f'Unsupported method: {method}'}

            return response.json()
        except http_requests.RequestException as e:
            _logger.error(f"API request failed: {e}")
            return {'error': str(e)}

    @http.route('/ailigent/tasks/health', type='json', auth='user', methods=['POST'])
    def health_check(self):
        """Check API health."""
        return self._make_api_request('GET', '/api/v1/health')

    @http.route('/ailigent/tasks/analyze-workload', type='json', auth='user', methods=['POST'])
    def analyze_workload(self, employees, tasks, weekly_capacity=40):
        """Analyze team workload."""
        data = {
            'employees': employees,
            'tasks': tasks,
            'weekly_capacity': weekly_capacity,
        }
        return self._make_api_request('POST', '/api/v1/distribution/analyze-workload', data, timeout=120)

    @http.route('/ailigent/tasks/recommend-assignment', type='json', auth='user', methods=['POST'])
    def recommend_assignment(self, task, employees):
        """Get AI recommendation for task assignment."""
        data = {
            'task': task,
            'available_employees': employees,
        }
        return self._make_api_request('POST', '/api/v1/distribution/recommend-assignment', data)

    @http.route('/ailigent/tasks/detect-bottlenecks', type='json', auth='user', methods=['POST'])
    def detect_bottlenecks(self, workflow_data):
        """Detect workflow bottlenecks."""
        data = {
            'workflow_data': workflow_data,
        }
        return self._make_api_request('POST', '/api/v1/distribution/detect-bottlenecks', data, timeout=120)

    @http.route('/ailigent/tasks/productivity-report', type='json', auth='user', methods=['POST'])
    def get_productivity_report(self, metrics):
        """Generate productivity report."""
        data = {
            'metrics': metrics,
        }
        return self._make_api_request('POST', '/api/v1/reports/productivity', data, timeout=120)
