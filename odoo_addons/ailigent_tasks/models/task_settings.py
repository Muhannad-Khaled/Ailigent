"""Task Settings Model - API Configuration."""

from odoo import models, fields, api


class TaskSettings(models.Model):
    """Settings for Ailigent Task API connection."""

    _name = 'ailigent.task.settings'
    _description = 'Ailigent Task Settings'

    name = fields.Char(
        string='Configuration Name',
        default='Default',
        required=True,
    )
    api_url = fields.Char(
        string='API URL',
        help='URL of the Task Management FastAPI service (e.g., http://localhost:8000)',
        default='http://localhost:8000',
    )
    api_key = fields.Char(
        string='API Key',
    )
    active = fields.Boolean(default=True)

    @api.model
    def get_settings(self):
        """Get active settings."""
        settings = self.search([('active', '=', True)], limit=1)
        if not settings:
            settings = self.create({
                'name': 'Default',
                'api_url': 'http://localhost:8000',
                'active': True,
            })
        return settings

    def action_test_connection(self):
        """Test API connection."""
        import requests
        from odoo.exceptions import UserError

        self.ensure_one()
        if not self.api_url:
            raise UserError('Please configure the API URL first.')

        try:
            url = f"{self.api_url.rstrip('/')}/api/v1/health"
            headers = {}
            if self.api_key:
                headers['X-API-Key'] = self.api_key

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Connected to Task Management API.',
                        'type': 'success',
                    }
                }
            else:
                raise UserError(f"API returned status {response.status_code}")

        except requests.RequestException as e:
            raise UserError(f"Connection failed: {str(e)}")
