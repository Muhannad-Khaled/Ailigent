"""Voice Session Model - Track voice assistant sessions."""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class VoiceSession(models.Model):
    """Model to track voice assistant sessions and transcripts."""

    _name = 'ailigent.voice.session'
    _description = 'Voice Session'
    _order = 'start_time desc'

    name = fields.Char(
        string='Session ID',
        required=True,
        readonly=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        readonly=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        readonly=True,
    )

    # Session Timing
    start_time = fields.Datetime(
        string='Start Time',
        readonly=True,
        default=fields.Datetime.now,
    )
    end_time = fields.Datetime(
        string='End Time',
        readonly=True,
    )
    duration_seconds = fields.Integer(
        string='Duration (seconds)',
        compute='_compute_duration',
        store=True,
    )
    duration_display = fields.Char(
        string='Duration',
        compute='_compute_duration',
    )

    # Session State
    state = fields.Selection([
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('error', 'Error'),
        ('disconnected', 'Disconnected'),
    ], string='Status', default='active', readonly=True)

    # Language
    language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('mixed', 'Mixed'),
    ], string='Language Used', readonly=True)

    # Transcript
    transcript_data = fields.Text(
        string='Transcript (JSON)',
        readonly=True,
        help='Full conversation transcript in JSON format',
    )
    transcript_display = fields.Html(
        string='Transcript',
        compute='_compute_transcript_display',
    )

    # Summary
    summary = fields.Text(
        string='Session Summary',
        readonly=True,
        help='AI-generated summary of the conversation',
    )

    # Metrics
    user_turns = fields.Integer(string='User Turns', readonly=True)
    assistant_turns = fields.Integer(string='Assistant Turns', readonly=True)
    total_words = fields.Integer(string='Total Words', readonly=True)

    # Room Info
    room_name = fields.Char(string='Room Name', readonly=True)
    participant_identity = fields.Char(string='Participant', readonly=True)

    # Error Info
    error_message = fields.Text(string='Error Details', readonly=True)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration_seconds = int(delta.total_seconds())
                minutes, seconds = divmod(record.duration_seconds, 60)
                record.duration_display = f"{minutes}m {seconds}s"
            else:
                record.duration_seconds = 0
                record.duration_display = "In Progress" if record.state == 'active' else "N/A"

    @api.depends('transcript_data')
    def _compute_transcript_display(self):
        import json
        for record in self:
            if record.transcript_data:
                try:
                    transcript = json.loads(record.transcript_data)
                    html = '<div class="voice-transcript">'
                    for entry in transcript:
                        role = entry.get('role', 'unknown')
                        text = entry.get('text', '')
                        timestamp = entry.get('timestamp', '')

                        if role == 'user':
                            html += f'''
                            <div class="mb-2 p-2 bg-light rounded">
                                <small class="text-muted">{timestamp}</small>
                                <div><strong>User:</strong> {text}</div>
                            </div>
                            '''
                        else:
                            html += f'''
                            <div class="mb-2 p-2 bg-info bg-opacity-10 rounded">
                                <small class="text-muted">{timestamp}</small>
                                <div><strong>Assistant:</strong> {text}</div>
                            </div>
                            '''
                    html += '</div>'
                    record.transcript_display = html
                except Exception:
                    record.transcript_display = '<p>Unable to parse transcript</p>'
            else:
                record.transcript_display = '<p class="text-muted">No transcript available</p>'

    @api.model
    def create_from_webhook(self, data):
        """Create session from webhook data."""
        vals = {
            'name': data.get('session_id', f"session-{fields.Datetime.now()}"),
            'room_name': data.get('room_name'),
            'participant_identity': data.get('participant_identity'),
            'language': data.get('language', 'en'),
            'state': data.get('state', 'active'),
        }

        # Find user/employee
        participant = data.get('participant_identity', '')
        if participant:
            user = self.env['res.users'].search([
                '|',
                ('login', '=', participant),
                ('email', '=', participant),
            ], limit=1)
            if user:
                vals['user_id'] = user.id
                employee = self.env['hr.employee'].search([
                    ('user_id', '=', user.id)
                ], limit=1)
                if employee:
                    vals['employee_id'] = employee.id

        return self.create(vals)

    def update_from_webhook(self, data):
        """Update session from webhook data."""
        import json

        vals = {}

        if data.get('state'):
            vals['state'] = data['state']

        if data.get('end_time'):
            vals['end_time'] = data['end_time']

        if data.get('transcript'):
            vals['transcript_data'] = json.dumps(data['transcript'])

        if data.get('summary'):
            vals['summary'] = data['summary']

        if data.get('metrics'):
            metrics = data['metrics']
            vals['user_turns'] = metrics.get('user_turns', 0)
            vals['assistant_turns'] = metrics.get('assistant_turns', 0)
            vals['total_words'] = metrics.get('total_words', 0)

        if data.get('error'):
            vals['state'] = 'error'
            vals['error_message'] = data['error']

        if vals:
            self.write(vals)

        return True
