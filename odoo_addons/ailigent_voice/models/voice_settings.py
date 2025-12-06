"""Voice Settings Model - Configuration for AI voice assistant."""

from odoo import models, fields, api


class VoiceSettings(models.Model):
    """Settings for Ailigent Voice Assistant."""

    _name = 'ailigent.voice.settings'
    _description = 'Ailigent Voice Settings'

    name = fields.Char(
        string='Configuration Name',
        default='Default',
        required=True,
    )

    # API Configuration
    api_url = fields.Char(
        string='API URL',
        help='URL of the Voice Agent FastAPI service (e.g., http://localhost:8004)',
        default='http://localhost:8004',
    )
    api_key = fields.Char(
        string='API Key',
    )

    # LiveKit Configuration
    livekit_url = fields.Char(
        string='LiveKit Server URL',
        help='WebSocket URL for LiveKit server',
    )

    # Voice Preferences
    default_language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('en-ar', 'Bilingual (English/Arabic)'),
    ], string='Default Language', default='en')

    voice_persona = fields.Selection([
        ('professional', 'Professional'),
        ('friendly', 'Friendly'),
        ('concise', 'Concise'),
    ], string='Voice Persona', default='professional')

    # TTS Settings
    tts_provider = fields.Selection([
        ('openai', 'OpenAI TTS'),
        ('elevenlabs', 'ElevenLabs'),
        ('google', 'Google TTS'),
    ], string='TTS Provider', default='openai')

    tts_voice = fields.Char(
        string='TTS Voice ID',
        help='Voice ID for the selected TTS provider',
        default='alloy',
    )

    # STT Settings
    stt_provider = fields.Selection([
        ('deepgram', 'Deepgram'),
        ('openai', 'OpenAI Whisper'),
        ('google', 'Google Speech'),
    ], string='STT Provider', default='deepgram')

    active = fields.Boolean(default=True)

    @api.model
    def get_settings(self):
        """Get active settings."""
        settings = self.search([('active', '=', True)], limit=1)
        if not settings:
            settings = self.create({
                'name': 'Default',
                'api_url': 'http://localhost:8004',
                'active': True,
            })
        return settings

    def action_test_connection(self):
        """Test connection to the Voice API."""
        import requests
        from odoo.exceptions import UserError

        self.ensure_one()
        if not self.api_url:
            raise UserError('Please configure the API URL first.')

        try:
            url = f"{self.api_url.rstrip('/')}/health"
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Connected to Voice Agent API.',
                        'type': 'success',
                    }
                }
            else:
                raise UserError(f"API returned status {response.status_code}")

        except requests.RequestException as e:
            raise UserError(f"Connection failed: {str(e)}")


class VoiceUserPreference(models.Model):
    """Per-user voice preferences."""

    _name = 'ailigent.voice.user.preference'
    _description = 'User Voice Preferences'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        compute='_compute_employee_id',
        store=True,
    )

    language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('en-ar', 'Bilingual'),
    ], string='Preferred Language', default='en')

    voice_persona = fields.Selection([
        ('professional', 'Professional'),
        ('friendly', 'Friendly'),
        ('concise', 'Concise'),
    ], string='Voice Persona', default='professional')

    speech_rate = fields.Selection([
        ('slow', 'Slow'),
        ('normal', 'Normal'),
        ('fast', 'Fast'),
    ], string='Speech Rate', default='normal')

    @api.depends('user_id')
    def _compute_employee_id(self):
        for record in self:
            employee = self.env['hr.employee'].search([
                ('user_id', '=', record.user_id.id)
            ], limit=1)
            record.employee_id = employee.id if employee else False

    _sql_constraints = [
        ('user_unique', 'unique(user_id)', 'Each user can only have one voice preference record.')
    ]
