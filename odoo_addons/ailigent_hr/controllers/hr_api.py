"""HR API Controller - Proxy to FastAPI backend."""

import json
import logging
from odoo import http
from odoo.http import request
import requests as http_requests

_logger = logging.getLogger(__name__)


class HRAPIController(http.Controller):
    """Controller to proxy requests to the HR Agent FastAPI service."""

    def _get_api_settings(self):
        """Get API settings."""
        return request.env['ailigent.hr.settings'].sudo().get_settings()

    def _make_api_request(self, method, endpoint, data=None, timeout=60):
        """Make request to the FastAPI backend."""
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

    @http.route('/ailigent/hr/health', type='json', auth='user', methods=['POST'])
    def health_check(self):
        """Check API health."""
        return self._make_api_request('GET', '/api/v1/health')

    @http.route('/ailigent/hr/analyze-cv', type='json', auth='user', methods=['POST'])
    def analyze_cv(self, cv_text, job_requirements=''):
        """Analyze a CV."""
        data = {
            'cv_text': cv_text,
            'job_requirements': job_requirements,
        }
        return self._make_api_request('POST', '/api/v1/recruitment/analyze-cv', data, timeout=120)

    @http.route('/ailigent/hr/rank-candidates', type='json', auth='user', methods=['POST'])
    def rank_candidates(self, job_description, candidates):
        """Rank multiple candidates."""
        data = {
            'job_description': job_description,
            'candidates': candidates,
        }
        return self._make_api_request('POST', '/api/v1/recruitment/rank-candidates', data, timeout=120)

    @http.route('/ailigent/hr/generate-insights', type='json', auth='user', methods=['POST'])
    def generate_insights(self, metrics, report_type='overview'):
        """Generate HR insights."""
        data = {
            'metrics': metrics,
            'report_type': report_type,
        }
        return self._make_api_request('POST', '/api/v1/reports/insights', data, timeout=120)

    @http.route('/ailigent/hr/interview-questions', type='json', auth='user', methods=['POST'])
    def generate_interview_questions(self, cv_analysis, job_requirements):
        """Generate interview questions."""
        data = {
            'cv_analysis': cv_analysis,
            'job_requirements': job_requirements,
        }
        return self._make_api_request('POST', '/api/v1/recruitment/interview-questions', data)
