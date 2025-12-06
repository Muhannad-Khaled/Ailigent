"""Contract Analysis Model - Stores AI analysis results."""

from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class ContractAnalysis(models.Model):
    """Model to store contract AI analysis results."""

    _name = 'ailigent.contract.analysis'
    _description = 'Contract AI Analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Contract Name',
        required=True,
        tracking=True,
    )
    contract_text = fields.Text(
        string='Contract Text',
        help='Full text of the contract for analysis',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Contract Documents',
        help='Upload contract documents (PDF, DOCX)',
    )

    # AI Analysis Results
    state = fields.Selection([
        ('draft', 'Draft'),
        ('analyzing', 'Analyzing'),
        ('analyzed', 'Analyzed'),
        ('error', 'Error'),
    ], string='Status', default='draft', tracking=True)

    summary = fields.Text(
        string='AI Summary',
        readonly=True,
    )
    contract_type = fields.Char(
        string='Contract Type',
        readonly=True,
    )
    overall_risk_score = fields.Float(
        string='Overall Risk Score',
        readonly=True,
        help='Risk score from 0-100',
    )
    overall_risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Risk Level', readonly=True)

    # Structured data stored as JSON
    parties_data = fields.Text(
        string='Parties (JSON)',
        readonly=True,
    )
    key_dates_data = fields.Text(
        string='Key Dates (JSON)',
        readonly=True,
    )
    financial_terms_data = fields.Text(
        string='Financial Terms (JSON)',
        readonly=True,
    )
    clauses_data = fields.Text(
        string='Clauses (JSON)',
        readonly=True,
    )
    risks_data = fields.Text(
        string='Risks (JSON)',
        readonly=True,
    )
    recommendations_data = fields.Text(
        string='Recommendations (JSON)',
        readonly=True,
    )
    compliance_data = fields.Text(
        string='Compliance Issues (JSON)',
        readonly=True,
    )

    # Computed display fields
    parties_display = fields.Html(
        string='Parties',
        compute='_compute_parties_display',
    )
    clauses_display = fields.Html(
        string='Key Clauses',
        compute='_compute_clauses_display',
    )
    risks_display = fields.Html(
        string='Identified Risks',
        compute='_compute_risks_display',
    )
    recommendations_display = fields.Html(
        string='Recommendations',
        compute='_compute_recommendations_display',
    )

    analysis_error = fields.Text(
        string='Analysis Error',
        readonly=True,
    )
    analyzed_at = fields.Datetime(
        string='Analyzed At',
        readonly=True,
    )

    @api.depends('parties_data')
    def _compute_parties_display(self):
        import json
        for record in self:
            if record.parties_data:
                try:
                    parties = json.loads(record.parties_data)
                    html = '<ul>'
                    for party in parties:
                        html += f"<li><strong>{party.get('name', 'N/A')}</strong> ({party.get('role', 'N/A')})"
                        if party.get('obligations'):
                            html += '<br/><em>Obligations:</em> ' + ', '.join(party['obligations'])
                        html += '</li>'
                    html += '</ul>'
                    record.parties_display = html
                except Exception:
                    record.parties_display = '<p>Unable to parse parties data</p>'
            else:
                record.parties_display = '<p>No parties identified</p>'

    @api.depends('clauses_data')
    def _compute_clauses_display(self):
        import json
        for record in self:
            if record.clauses_data:
                try:
                    clauses = json.loads(record.clauses_data)
                    html = '<table class="table table-sm"><thead><tr><th>Clause</th><th>Importance</th><th>Summary</th></tr></thead><tbody>'
                    for clause in clauses:
                        importance = clause.get('importance', 'medium')
                        badge_class = 'danger' if importance == 'critical' else 'warning' if importance == 'high' else 'info'
                        html += f"<tr><td>{clause.get('clause_type', 'N/A')}</td>"
                        html += f"<td><span class='badge bg-{badge_class}'>{importance}</span></td>"
                        html += f"<td>{clause.get('summary', 'N/A')}</td></tr>"
                    html += '</tbody></table>'
                    record.clauses_display = html
                except Exception:
                    record.clauses_display = '<p>Unable to parse clauses data</p>'
            else:
                record.clauses_display = '<p>No clauses identified</p>'

    @api.depends('risks_data')
    def _compute_risks_display(self):
        import json
        for record in self:
            if record.risks_data:
                try:
                    risks = json.loads(record.risks_data)
                    html = '<div class="row">'
                    for risk in risks:
                        severity = risk.get('severity', 'low')
                        color = 'danger' if severity in ['high', 'critical'] else 'warning' if severity == 'medium' else 'success'
                        html += f'''
                        <div class="col-md-6 mb-2">
                            <div class="card border-{color}">
                                <div class="card-body p-2">
                                    <h6 class="card-title text-{color}">{risk.get('risk_type', 'N/A')}</h6>
                                    <p class="card-text small">{risk.get('description', 'N/A')}</p>
                                    <p class="card-text small"><em>Mitigation: {risk.get('mitigation', 'N/A')}</em></p>
                                </div>
                            </div>
                        </div>
                        '''
                    html += '</div>'
                    record.risks_display = html
                except Exception:
                    record.risks_display = '<p>Unable to parse risks data</p>'
            else:
                record.risks_display = '<p>No risks identified</p>'

    @api.depends('recommendations_data')
    def _compute_recommendations_display(self):
        import json
        for record in self:
            if record.recommendations_data:
                try:
                    recs = json.loads(record.recommendations_data)
                    html = '<ol>'
                    for rec in recs:
                        html += f"<li>{rec}</li>"
                    html += '</ol>'
                    record.recommendations_display = html
                except Exception:
                    record.recommendations_display = '<p>Unable to parse recommendations</p>'
            else:
                record.recommendations_display = '<p>No recommendations</p>'

    def action_analyze(self):
        """Trigger AI analysis of the contract."""
        self.ensure_one()

        if not self.contract_text and not self.attachment_ids:
            raise UserError('Please provide contract text or upload a document.')

        self.write({'state': 'analyzing', 'analysis_error': False})

        # Get API settings
        settings = self.env['ailigent.contract.settings'].get_settings()
        if not settings.api_url:
            raise UserError('Contract API URL is not configured. Go to Settings > Ailigent > Contracts.')

        try:
            # Prepare request
            headers = {
                'X-API-Key': settings.api_key or '',
                'Content-Type': 'application/json',
            }

            # If we have attachments, we need to extract text first
            contract_text = self.contract_text or ''
            if not contract_text and self.attachment_ids:
                # For now, just indicate attachment analysis is needed
                contract_text = "[Contract document attached - text extraction required]"

            payload = {
                'contract_text': contract_text,
                'contract_name': self.name,
            }

            # Call the FastAPI backend
            url = f"{settings.api_url.rstrip('/')}/api/v1/contracts/analyze"
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code == 200:
                result = response.json()
                self._process_analysis_result(result)
            else:
                self.write({
                    'state': 'error',
                    'analysis_error': f"API Error: {response.status_code} - {response.text[:500]}",
                })

        except requests.RequestException as e:
            _logger.error(f"Contract analysis API error: {e}")
            self.write({
                'state': 'error',
                'analysis_error': f"Connection error: {str(e)}",
            })

        return True

    def _process_analysis_result(self, result):
        """Process the AI analysis result and update fields."""
        import json
        from datetime import datetime

        analysis = result.get('analysis', result)

        vals = {
            'state': 'analyzed',
            'analyzed_at': datetime.now(),
            'summary': analysis.get('summary', ''),
            'contract_type': analysis.get('contract_type', ''),
            'overall_risk_score': analysis.get('overall_risk_score', 0),
            'overall_risk_level': analysis.get('overall_risk_level', 'low'),
        }

        # Store structured data as JSON
        if analysis.get('parties'):
            vals['parties_data'] = json.dumps(analysis['parties'])
        if analysis.get('key_dates'):
            vals['key_dates_data'] = json.dumps(analysis['key_dates'])
        if analysis.get('financial_terms'):
            vals['financial_terms_data'] = json.dumps(analysis['financial_terms'])
        if analysis.get('clauses'):
            vals['clauses_data'] = json.dumps(analysis['clauses'])
        if analysis.get('risks'):
            vals['risks_data'] = json.dumps(analysis['risks'])
        if analysis.get('recommendations'):
            vals['recommendations_data'] = json.dumps(analysis['recommendations'])
        if analysis.get('compliance_issues'):
            vals['compliance_data'] = json.dumps(analysis['compliance_issues'])

        self.write(vals)

    def action_reset_draft(self):
        """Reset analysis to draft state."""
        self.ensure_one()
        self.write({
            'state': 'draft',
            'analysis_error': False,
            'summary': False,
            'contract_type': False,
            'overall_risk_score': 0,
            'overall_risk_level': False,
            'parties_data': False,
            'key_dates_data': False,
            'financial_terms_data': False,
            'clauses_data': False,
            'risks_data': False,
            'recommendations_data': False,
            'compliance_data': False,
            'analyzed_at': False,
        })
        return True
