"""HR Settings Model - API Configuration."""

from odoo import models, fields, api


class HRSettings(models.Model):
    """Settings for Ailigent HR API connection."""

    _name = 'ailigent.hr.settings'
    _description = 'Ailigent HR Settings'

    name = fields.Char(
        string='Configuration Name',
        default='Default',
        required=True,
    )
    api_url = fields.Char(
        string='API URL',
        help='URL of the HR Agent FastAPI service (e.g., http://localhost:8002)',
        default='http://localhost:8002',
    )
    api_key = fields.Char(
        string='API Key',
        help='API key for authentication with the HR Agent service',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    @api.model
    def get_settings(self):
        """Get the active settings record."""
        settings = self.search([('active', '=', True)], limit=1)
        if not settings:
            settings = self.create({
                'name': 'Default',
                'api_url': 'http://localhost:8002',
                'active': True,
            })
        return settings

    def action_test_connection(self):
        """Test connection to the API."""
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
                        'title': 'Connection Successful',
                        'message': 'Successfully connected to the HR Agent API.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(f"API returned status {response.status_code}")

        except requests.RequestException as e:
            raise UserError(f"Connection failed: {str(e)}")
