"""Contract Settings Model - API Configuration."""

from odoo import models, fields, api


class ContractSettings(models.Model):
    """Settings for Ailigent Contract API connection."""

    _name = 'ailigent.contract.settings'
    _description = 'Ailigent Contract Settings'

    name = fields.Char(
        string='Configuration Name',
        default='Default',
        required=True,
    )
    api_url = fields.Char(
        string='API URL',
        help='URL of the Contracts FastAPI service (e.g., http://localhost:8001)',
        default='http://localhost:8001',
    )
    api_key = fields.Char(
        string='API Key',
        help='API key for authentication with the Contracts service',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    @api.model
    def get_settings(self):
        """Get the active settings record, create default if none exists."""
        settings = self.search([('active', '=', True)], limit=1)
        if not settings:
            settings = self.create({
                'name': 'Default',
                'api_url': 'http://localhost:8001',
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
                        'message': 'Successfully connected to the Contracts API.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(f"API returned status {response.status_code}: {response.text[:200]}")

        except requests.RequestException as e:
            raise UserError(f"Connection failed: {str(e)}")
