"""Voice API Controller - Webhook handler for voice sessions."""

import json
import logging
from odoo import http
from odoo.http import request
import requests as http_requests

_logger = logging.getLogger(__name__)


class VoiceAPIController(http.Controller):
    """Controller to handle voice session webhooks and API proxy."""

    def _get_api_settings(self):
        """Get API settings."""
        return request.env['ailigent.voice.settings'].sudo().get_settings()

    def _make_api_request(self, method, endpoint, data=None, timeout=30):
        """Make request to Voice Agent backend."""
        settings = self._get_api_settings()
        if not settings.api_url:
            return {'error': 'API URL not configured'}

        url = f"{settings.api_url.rstrip('/')}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if settings.api_key:
            headers['Authorization'] = f'Bearer {settings.api_key}'

        try:
            if method == 'GET':
                response = http_requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = http_requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return {'error': f'Unsupported method: {method}'}

            return response.json()
        except http_requests.RequestException as e:
            _logger.error(f"Voice API request failed: {e}")
            return {'error': str(e)}

    @http.route('/ailigent/voice/health', type='json', auth='user', methods=['POST'])
    def health_check(self):
        """Check Voice API health."""
        return self._make_api_request('GET', '/health')

    @http.route('/ailigent/voice/webhook/session', type='json', auth='public', methods=['POST'], csrf=False)
    def session_webhook(self):
        """Handle session webhooks from Voice Agent."""
        try:
            data = request.jsonrequest

            event_type = data.get('event_type')
            session_id = data.get('session_id')

            if not session_id:
                return {'error': 'Missing session_id'}

            VoiceSession = request.env['ailigent.voice.session'].sudo()

            if event_type == 'session_started':
                # Create new session
                session = VoiceSession.create_from_webhook(data)
                _logger.info(f"Voice session started: {session.name}")
                return {'status': 'created', 'id': session.id}

            elif event_type in ['session_ended', 'session_updated', 'session_error']:
                # Find and update existing session
                session = VoiceSession.search([('name', '=', session_id)], limit=1)
                if session:
                    session.update_from_webhook(data)
                    _logger.info(f"Voice session updated: {session.name}")
                    return {'status': 'updated', 'id': session.id}
                else:
                    _logger.warning(f"Session not found: {session_id}")
                    return {'error': 'Session not found'}

            else:
                _logger.warning(f"Unknown webhook event type: {event_type}")
                return {'error': f'Unknown event type: {event_type}'}

        except Exception as e:
            _logger.error(f"Voice webhook error: {e}")
            return {'error': str(e)}

    @http.route('/ailigent/voice/get-token', type='json', auth='user', methods=['POST'])
    def get_token(self, room_name=None):
        """Get LiveKit token for voice session."""
        user = request.env.user
        employee = request.env['hr.employee'].search([
            ('user_id', '=', user.id)
        ], limit=1)

        data = {
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email or user.login,
            'employee_id': employee.id if employee else None,
            'room_name': room_name,
        }

        # Get user preferences
        preference = request.env['ailigent.voice.user.preference'].search([
            ('user_id', '=', user.id)
        ], limit=1)

        if preference:
            data['language'] = preference.language
            data['voice_persona'] = preference.voice_persona
            data['speech_rate'] = preference.speech_rate

        return self._make_api_request('POST', '/api/get-token', data)

    @http.route('/ailigent/voice/sessions', type='json', auth='user', methods=['POST'])
    def list_sessions(self, limit=20):
        """List user's voice sessions."""
        user = request.env.user
        sessions = request.env['ailigent.voice.session'].search([
            ('user_id', '=', user.id)
        ], limit=limit, order='start_time desc')

        return [{
            'id': s.id,
            'name': s.name,
            'start_time': s.start_time.isoformat() if s.start_time else None,
            'duration': s.duration_display,
            'state': s.state,
            'language': s.language,
        } for s in sessions]
