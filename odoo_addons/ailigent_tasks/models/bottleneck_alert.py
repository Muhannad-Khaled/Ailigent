"""Bottleneck Alert Model - Workflow bottleneck detection."""

from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class BottleneckAlert(models.Model):
    """Model to store bottleneck detection results."""

    _name = 'ailigent.bottleneck.alert'
    _description = 'Workflow Bottleneck Alert'
    _order = 'severity_order desc, create_date desc'

    name = fields.Char(
        string='Alert Name',
        required=True,
        default=lambda self: f"Bottleneck Analysis - {fields.Datetime.now()}",
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('analyzing', 'Analyzing'),
        ('analyzed', 'Analyzed'),
        ('resolved', 'Resolved'),
        ('error', 'Error'),
    ], string='Status', default='draft')

    # Filter
    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
    )

    # Analysis Results
    bottlenecks_count = fields.Integer(
        string='Bottlenecks Found',
        compute='_compute_bottlenecks_count',
    )
    summary = fields.Text(string='Summary', readonly=True)

    # Structured Data
    bottlenecks_data = fields.Text(string='Bottlenecks (JSON)', readonly=True)
    patterns_data = fields.Text(string='Patterns (JSON)', readonly=True)
    priority_actions_data = fields.Text(string='Priority Actions (JSON)', readonly=True)

    # Display Fields
    bottlenecks_display = fields.Html(string='Bottlenecks', compute='_compute_bottlenecks_display')
    actions_display = fields.Html(string='Priority Actions', compute='_compute_actions_display')

    severity_order = fields.Integer(compute='_compute_severity_order', store=True)
    analysis_error = fields.Text(readonly=True)
    analyzed_at = fields.Datetime(readonly=True)

    @api.depends('bottlenecks_data')
    def _compute_bottlenecks_count(self):
        import json
        for record in self:
            if record.bottlenecks_data:
                try:
                    bottlenecks = json.loads(record.bottlenecks_data)
                    record.bottlenecks_count = len(bottlenecks)
                except Exception:
                    record.bottlenecks_count = 0
            else:
                record.bottlenecks_count = 0

    @api.depends('bottlenecks_data')
    def _compute_severity_order(self):
        import json
        severity_map = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        for record in self:
            max_severity = 0
            if record.bottlenecks_data:
                try:
                    bottlenecks = json.loads(record.bottlenecks_data)
                    for b in bottlenecks:
                        sev = severity_map.get(b.get('severity', 'low'), 1)
                        max_severity = max(max_severity, sev)
                except Exception:
                    pass
            record.severity_order = max_severity

    @api.depends('bottlenecks_data')
    def _compute_bottlenecks_display(self):
        import json
        for record in self:
            if record.bottlenecks_data:
                try:
                    bottlenecks = json.loads(record.bottlenecks_data)
                    html = ''
                    for b in bottlenecks:
                        severity = b.get('severity', 'low')
                        color = 'danger' if severity in ['critical', 'high'] else 'warning' if severity == 'medium' else 'info'
                        html += f'''
                        <div class="card mb-2 border-{color}">
                            <div class="card-header bg-{color} text-white">
                                <strong>{b.get('type', 'N/A').title()} Bottleneck</strong>
                                <span class="badge bg-light text-dark float-end">{severity.upper()}</span>
                            </div>
                            <div class="card-body">
                                <p><strong>Location:</strong> {b.get('location', 'N/A')}</p>
                                <p><strong>Impact:</strong> {b.get('impact', 'N/A')}</p>
                                <p><strong>Root Cause:</strong> {b.get('root_cause', 'N/A')}</p>
                                <p class="mb-0"><strong>Recommendation:</strong> {b.get('recommendation', 'N/A')}</p>
                            </div>
                        </div>
                        '''
                    record.bottlenecks_display = html if html else '<p>No bottlenecks found</p>'
                except Exception:
                    record.bottlenecks_display = '<p>Unable to parse</p>'
            else:
                record.bottlenecks_display = '<p class="text-success">No bottlenecks detected</p>'

    @api.depends('priority_actions_data')
    def _compute_actions_display(self):
        import json
        for record in self:
            if record.priority_actions_data:
                try:
                    actions = json.loads(record.priority_actions_data)
                    html = '<ol class="list-group list-group-numbered">'
                    for action in actions:
                        html += f'<li class="list-group-item">{action}</li>'
                    html += '</ol>'
                    record.actions_display = html
                except Exception:
                    record.actions_display = '<p>Unable to parse</p>'
            else:
                record.actions_display = '<p>No actions identified</p>'

    def action_analyze(self):
        """Trigger bottleneck detection."""
        self.ensure_one()
        self.write({'state': 'analyzing', 'analysis_error': False})

        settings = self.env['ailigent.task.settings'].get_settings()
        if not settings.api_url:
            raise UserError('Task API URL is not configured.')

        try:
            headers = {
                'X-API-Key': settings.api_key or '',
                'Content-Type': 'application/json',
            }

            workflow_data = self._gather_workflow_data()

            payload = {
                'workflow_data': workflow_data,
            }

            url = f"{settings.api_url.rstrip('/')}/api/v1/distribution/detect-bottlenecks"
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code == 200:
                result = response.json()
                self._process_analysis_result(result)
            else:
                self.write({
                    'state': 'error',
                    'analysis_error': f"API Error: {response.status_code}",
                })

        except requests.RequestException as e:
            _logger.error(f"Bottleneck detection error: {e}")
            self.write({
                'state': 'error',
                'analysis_error': str(e),
            })

        return True

    def _gather_workflow_data(self):
        """Gather workflow data for bottleneck analysis."""
        Task = self.env['project.task']
        Stage = self.env['project.task.type']

        domain = []
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))

        tasks = Task.search(domain, limit=1000)

        # Group tasks by stage
        stage_data = {}
        for task in tasks:
            stage_name = task.stage_id.name if task.stage_id else 'No Stage'
            if stage_name not in stage_data:
                stage_data[stage_name] = {
                    'count': 0,
                    'total_days': 0,
                    'overdue_count': 0,
                }
            stage_data[stage_name]['count'] += 1
            if task.date_deadline and task.date_deadline < fields.Date.today():
                stage_data[stage_name]['overdue_count'] += 1

        return {
            'total_tasks': len(tasks),
            'stages': stage_data,
            'projects': [{'id': p.id, 'name': p.name} for p in self.project_ids] if self.project_ids else [],
        }

    def _process_analysis_result(self, result):
        """Process analysis result."""
        import json
        from datetime import datetime

        analysis = result.get('analysis', result)

        vals = {
            'state': 'analyzed',
            'analyzed_at': datetime.now(),
            'summary': analysis.get('summary', ''),
        }

        if analysis.get('bottlenecks'):
            vals['bottlenecks_data'] = json.dumps(analysis['bottlenecks'])
        if analysis.get('patterns'):
            vals['patterns_data'] = json.dumps(analysis['patterns'])
        if analysis.get('priority_actions'):
            vals['priority_actions_data'] = json.dumps(analysis['priority_actions'])

        self.write(vals)

    def action_resolve(self):
        """Mark as resolved."""
        self.write({'state': 'resolved'})
