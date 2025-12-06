"""Contract API Controller - Proxy to FastAPI backend."""

import json
import logging
from odoo import http
from odoo.http import request
import requests as http_requests

_logger = logging.getLogger(__name__)


class ContractAPIController(http.Controller):
    """Controller to proxy requests to the Contracts FastAPI service."""

    def _get_api_settings(self):
        """Get API settings."""
        return request.env['ailigent.contract.settings'].sudo().get_settings()

    def _make_api_request(self, method, endpoint, data=None, timeout=60):
        """Make request to the FastAPI backend."""
        settings = self._get_api_settings()
        if not settings.api_url:
            return {'error': 'API URL not configured'}

        url = f"{settings.api_url.rstrip('/')}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
        }
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

    @http.route('/ailigent/contracts/health', type='json', auth='user', methods=['POST'])
    def health_check(self):
        """Check API health."""
        return self._make_api_request('GET', '/api/v1/health')

    @http.route('/ailigent/contracts/analyze', type='json', auth='user', methods=['POST'])
    def analyze_contract(self, contract_text, contract_name=''):
        """Analyze a contract via API."""
        data = {
            'contract_text': contract_text,
            'contract_name': contract_name,
        }
        return self._make_api_request('POST', '/api/v1/contracts/analyze', data, timeout=120)

    @http.route('/ailigent/contracts/compare', type='json', auth='user', methods=['POST'])
    def compare_contracts(self, contract_text_1, contract_text_2):
        """Compare two contracts."""
        data = {
            'contract_text_1': contract_text_1,
            'contract_text_2': contract_text_2,
        }
        return self._make_api_request('POST', '/api/v1/contracts/compare', data, timeout=120)

    @http.route('/ailigent/contracts/extract-dates', type='json', auth='user', methods=['POST'])
    def extract_dates(self, contract_text):
        """Extract key dates from contract."""
        data = {
            'contract_text': contract_text,
        }
        return self._make_api_request('POST', '/api/v1/contracts/extract-dates', data)

    @http.route('/ailigent/contracts/summarize', type='json', auth='user', methods=['POST'])
    def summarize_contract(self, contract_text, max_length=500):
        """Get contract summary."""
        data = {
            'contract_text': contract_text,
            'max_length': max_length,
        }
        return self._make_api_request('POST', '/api/v1/contracts/summarize', data)
