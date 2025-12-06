"""HR Insights Model - AI-generated HR analytics."""

from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class HRInsights(models.Model):
    """Model to store AI-generated HR insights."""

    _name = 'ailigent.hr.insights'
    _description = 'AI HR Insights'
    _order = 'create_date desc'

    name = fields.Char(
        string='Report Name',
        required=True,
        default=lambda self: f"HR Insights - {fields.Date.today()}",
    )
    report_type = fields.Selection([
        ('overview', 'General Overview'),
        ('recruitment', 'Recruitment Analysis'),
        ('attendance', 'Attendance Analysis'),
        ('turnover', 'Turnover Analysis'),
        ('performance', 'Performance Analysis'),
    ], string='Report Type', default='overview', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('generated', 'Generated'),
        ('error', 'Error'),
    ], string='Status', default='draft')

    # Date Range
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date', default=fields.Date.today)

    # Department Filter
    department_ids = fields.Many2many(
        'hr.department',
        string='Departments',
        help='Leave empty for all departments',
    )

    # AI Generated Content
    executive_summary = fields.Text(string='Executive Summary', readonly=True)
    key_findings_data = fields.Text(string='Key Findings (JSON)', readonly=True)
    recommendations_data = fields.Text(string='Recommendations (JSON)', readonly=True)
    risks_data = fields.Text(string='Identified Risks (JSON)', readonly=True)
    metrics_data = fields.Text(string='Metrics (JSON)', readonly=True)

    # Display Fields
    key_findings_display = fields.Html(string='Key Findings', compute='_compute_key_findings_display')
    recommendations_display = fields.Html(string='Recommendations', compute='_compute_recommendations_display')
    metrics_display = fields.Html(string='Key Metrics', compute='_compute_metrics_display')

    analysis_error = fields.Text(string='Error', readonly=True)
    generated_at = fields.Datetime(string='Generated At', readonly=True)

    @api.depends('key_findings_data')
    def _compute_key_findings_display(self):
        import json
        for record in self:
            if record.key_findings_data:
                try:
                    findings = json.loads(record.key_findings_data)
                    html = '<ul>'
                    for f in findings:
                        html += f'<li>{f}</li>'
                    html += '</ul>'
                    record.key_findings_display = html
                except Exception:
                    record.key_findings_display = '<p>Unable to parse</p>'
            else:
                record.key_findings_display = '<p>No findings</p>'

    @api.depends('recommendations_data')
    def _compute_recommendations_display(self):
        import json
        for record in self:
            if record.recommendations_data:
                try:
                    recs = json.loads(record.recommendations_data)
                    html = '<ol>'
                    for r in recs:
                        html += f'<li>{r}</li>'
                    html += '</ol>'
                    record.recommendations_display = html
                except Exception:
                    record.recommendations_display = '<p>Unable to parse</p>'
            else:
                record.recommendations_display = '<p>No recommendations</p>'

    @api.depends('metrics_data')
    def _compute_metrics_display(self):
        import json
        for record in self:
            if record.metrics_data:
                try:
                    metrics = json.loads(record.metrics_data)
                    html = '<div class="row">'
                    for key, value in metrics.items():
                        html += f'''
                        <div class="col-md-3 text-center mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h3>{value}</h3>
                                    <p class="text-muted">{key.replace('_', ' ').title()}</p>
                                </div>
                            </div>
                        </div>
                        '''
                    html += '</div>'
                    record.metrics_display = html
                except Exception:
                    record.metrics_display = '<p>Unable to parse</p>'
            else:
                record.metrics_display = '<p>No metrics</p>'

    def action_generate(self):
        """Generate AI insights report."""
        self.ensure_one()
        self.write({'state': 'generating', 'analysis_error': False})

        settings = self.env['ailigent.hr.settings'].get_settings()
        if not settings.api_url:
            raise UserError('HR API URL is not configured.')

        try:
            headers = {
                'X-API-Key': settings.api_key or '',
                'Content-Type': 'application/json',
            }

            # Gather HR metrics from Odoo
            metrics = self._gather_hr_metrics()

            payload = {
                'report_type': self.report_type,
                'metrics': metrics,
                'date_from': str(self.date_from) if self.date_from else None,
                'date_to': str(self.date_to) if self.date_to else None,
            }

            url = f"{settings.api_url.rstrip('/')}/api/v1/reports/insights"
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code == 200:
                result = response.json()
                self._process_insights_result(result)
            else:
                self.write({
                    'state': 'error',
                    'analysis_error': f"API Error: {response.status_code}",
                })

        except requests.RequestException as e:
            _logger.error(f"HR insights API error: {e}")
            self.write({
                'state': 'error',
                'analysis_error': str(e),
            })

        return True

    def _gather_hr_metrics(self):
        """Gather HR metrics from Odoo for AI analysis."""
        Employee = self.env['hr.employee']

        domain = []
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))

        employees = Employee.search(domain)

        metrics = {
            'total_employees': len(employees),
            'departments': len(employees.mapped('department_id')),
            'report_type': self.report_type,
        }

        # Add recruitment metrics if available
        if self.report_type in ['overview', 'recruitment']:
            Applicant = self.env.get('hr.applicant')
            if Applicant:
                applicant_domain = []
                if self.date_from:
                    applicant_domain.append(('create_date', '>=', self.date_from))
                if self.date_to:
                    applicant_domain.append(('create_date', '<=', self.date_to))

                applicants = Applicant.search(applicant_domain)
                metrics['total_applicants'] = len(applicants)
                metrics['hired'] = len(applicants.filtered(lambda a: a.stage_id.hired_stage))

        return metrics

    def _process_insights_result(self, result):
        """Process AI insights result."""
        import json
        from datetime import datetime

        insights = result.get('insights', result)

        vals = {
            'state': 'generated',
            'generated_at': datetime.now(),
            'executive_summary': insights.get('executive_summary', ''),
        }

        if insights.get('key_findings'):
            vals['key_findings_data'] = json.dumps(insights['key_findings'])
        if insights.get('recommendations'):
            vals['recommendations_data'] = json.dumps(insights['recommendations'])
        if insights.get('risks'):
            vals['risks_data'] = json.dumps(insights['risks'])
        if insights.get('metrics'):
            vals['metrics_data'] = json.dumps(insights['metrics'])

        self.write(vals)
