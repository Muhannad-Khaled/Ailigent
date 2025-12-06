"""CV Analysis Model - Stores AI CV analysis results."""

from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging
import base64

_logger = logging.getLogger(__name__)


class CVAnalysis(models.Model):
    """Model to store CV AI analysis results."""

    _name = 'ailigent.cv.analysis'
    _description = 'CV AI Analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'overall_score desc, create_date desc'

    name = fields.Char(
        string='Candidate Name',
        required=True,
        tracking=True,
    )
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')

    # Link to Odoo applicant if exists
    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        ondelete='set null',
    )
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        required=True,
    )

    # CV Document
    cv_file = fields.Binary(
        string='CV File',
        attachment=True,
    )
    cv_filename = fields.Char(string='CV Filename')
    cv_text = fields.Text(
        string='Extracted CV Text',
        help='Text extracted from the CV document',
    )

    # Analysis State
    state = fields.Selection([
        ('draft', 'Pending'),
        ('analyzing', 'Analyzing'),
        ('analyzed', 'Analyzed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('error', 'Error'),
    ], string='Status', default='draft', tracking=True)

    # AI Analysis Results
    overall_score = fields.Integer(
        string='Overall Score',
        help='Score from 0-100',
        readonly=True,
    )
    hiring_recommendation = fields.Selection([
        ('strongly_recommend', 'Strongly Recommend'),
        ('recommend', 'Recommend'),
        ('consider', 'Consider'),
        ('do_not_recommend', 'Do Not Recommend'),
    ], string='Recommendation', readonly=True)

    # Skill Analysis (JSON stored)
    skills_matched_data = fields.Text(string='Matched Skills (JSON)', readonly=True)
    skills_missing_data = fields.Text(string='Missing Skills (JSON)', readonly=True)
    skill_match_percentage = fields.Float(string='Skill Match %', readonly=True)

    # Experience Analysis
    experience_summary = fields.Text(string='Experience Summary', readonly=True)
    years_experience = fields.Float(string='Years of Experience', readonly=True)
    experience_relevance = fields.Selection([
        ('highly_relevant', 'Highly Relevant'),
        ('relevant', 'Relevant'),
        ('somewhat_relevant', 'Somewhat Relevant'),
        ('not_relevant', 'Not Relevant'),
    ], string='Experience Relevance', readonly=True)

    # Education Analysis
    education_summary = fields.Text(string='Education Summary', readonly=True)
    education_match = fields.Boolean(string='Education Requirements Met', readonly=True)

    # AI Insights
    strengths_data = fields.Text(string='Strengths (JSON)', readonly=True)
    concerns_data = fields.Text(string='Concerns (JSON)', readonly=True)
    interview_questions_data = fields.Text(string='Suggested Interview Questions (JSON)', readonly=True)
    ai_notes = fields.Text(string='AI Analysis Notes', readonly=True)

    # Display Fields
    strengths_display = fields.Html(string='Strengths', compute='_compute_strengths_display')
    concerns_display = fields.Html(string='Concerns', compute='_compute_concerns_display')
    skills_display = fields.Html(string='Skills Analysis', compute='_compute_skills_display')
    interview_questions_display = fields.Html(string='Interview Questions', compute='_compute_interview_questions_display')

    analysis_error = fields.Text(string='Analysis Error', readonly=True)
    analyzed_at = fields.Datetime(string='Analyzed At', readonly=True)

    @api.depends('strengths_data')
    def _compute_strengths_display(self):
        import json
        for record in self:
            if record.strengths_data:
                try:
                    strengths = json.loads(record.strengths_data)
                    html = '<ul class="list-unstyled">'
                    for s in strengths:
                        html += f'<li><i class="fa fa-check-circle text-success"></i> {s}</li>'
                    html += '</ul>'
                    record.strengths_display = html
                except Exception:
                    record.strengths_display = '<p>Unable to parse</p>'
            else:
                record.strengths_display = '<p>No strengths identified</p>'

    @api.depends('concerns_data')
    def _compute_concerns_display(self):
        import json
        for record in self:
            if record.concerns_data:
                try:
                    concerns = json.loads(record.concerns_data)
                    html = '<ul class="list-unstyled">'
                    for c in concerns:
                        html += f'<li><i class="fa fa-exclamation-triangle text-warning"></i> {c}</li>'
                    html += '</ul>'
                    record.concerns_display = html
                except Exception:
                    record.concerns_display = '<p>Unable to parse</p>'
            else:
                record.concerns_display = '<p>No concerns identified</p>'

    @api.depends('skills_matched_data', 'skills_missing_data')
    def _compute_skills_display(self):
        import json
        for record in self:
            html = '<div class="row">'

            # Matched skills
            html += '<div class="col-md-6"><h6 class="text-success">Matched Skills</h6>'
            if record.skills_matched_data:
                try:
                    matched = json.loads(record.skills_matched_data)
                    for skill in matched:
                        html += f'<span class="badge bg-success me-1 mb-1">{skill}</span>'
                except Exception:
                    html += '<p>Unable to parse</p>'
            else:
                html += '<p>None</p>'
            html += '</div>'

            # Missing skills
            html += '<div class="col-md-6"><h6 class="text-danger">Missing Skills</h6>'
            if record.skills_missing_data:
                try:
                    missing = json.loads(record.skills_missing_data)
                    for skill in missing:
                        html += f'<span class="badge bg-danger me-1 mb-1">{skill}</span>'
                except Exception:
                    html += '<p>Unable to parse</p>'
            else:
                html += '<p>None</p>'
            html += '</div></div>'

            record.skills_display = html

    @api.depends('interview_questions_data')
    def _compute_interview_questions_display(self):
        import json
        for record in self:
            if record.interview_questions_data:
                try:
                    questions = json.loads(record.interview_questions_data)
                    html = '<ol>'
                    for q in questions:
                        html += f'<li>{q}</li>'
                    html += '</ol>'
                    record.interview_questions_display = html
                except Exception:
                    record.interview_questions_display = '<p>Unable to parse</p>'
            else:
                record.interview_questions_display = '<p>No questions generated</p>'

    def action_analyze(self):
        """Trigger AI analysis of the CV."""
        self.ensure_one()

        if not self.cv_text and not self.cv_file:
            raise UserError('Please provide CV text or upload a CV file.')

        self.write({'state': 'analyzing', 'analysis_error': False})

        # Get API settings
        settings = self.env['ailigent.hr.settings'].get_settings()
        if not settings.api_url:
            raise UserError('HR API URL is not configured. Go to Settings > Ailigent > HR.')

        try:
            headers = {
                'X-API-Key': settings.api_key or '',
                'Content-Type': 'application/json',
            }

            # Get job requirements
            job_requirements = ''
            if self.job_id:
                job_requirements = self.job_id.description or self.job_id.name

            payload = {
                'cv_text': self.cv_text or '',
                'job_requirements': job_requirements,
                'candidate_name': self.name,
            }

            url = f"{settings.api_url.rstrip('/')}/api/v1/recruitment/analyze-cv"
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
            _logger.error(f"CV analysis API error: {e}")
            self.write({
                'state': 'error',
                'analysis_error': f"Connection error: {str(e)}",
            })

        return True

    def _process_analysis_result(self, result):
        """Process the AI analysis result."""
        import json
        from datetime import datetime

        analysis = result.get('analysis', result)

        vals = {
            'state': 'analyzed',
            'analyzed_at': datetime.now(),
            'overall_score': analysis.get('overall_score', 0),
            'hiring_recommendation': analysis.get('hiring_recommendation', 'consider'),
            'skill_match_percentage': analysis.get('skill_match', {}).get('match_percentage', 0),
            'experience_summary': analysis.get('experience', {}).get('summary', ''),
            'years_experience': analysis.get('experience', {}).get('years', 0),
            'experience_relevance': analysis.get('experience', {}).get('relevance', 'somewhat_relevant'),
            'education_summary': analysis.get('education', {}).get('summary', ''),
            'education_match': analysis.get('education', {}).get('meets_requirements', False),
            'ai_notes': analysis.get('notes', ''),
        }

        # Store JSON data
        skill_match = analysis.get('skill_match', {})
        if skill_match.get('matched_skills'):
            vals['skills_matched_data'] = json.dumps(skill_match['matched_skills'])
        if skill_match.get('missing_skills'):
            vals['skills_missing_data'] = json.dumps(skill_match['missing_skills'])
        if analysis.get('strengths'):
            vals['strengths_data'] = json.dumps(analysis['strengths'])
        if analysis.get('concerns'):
            vals['concerns_data'] = json.dumps(analysis['concerns'])
        if analysis.get('interview_questions'):
            vals['interview_questions_data'] = json.dumps(analysis['interview_questions'])

        self.write(vals)

    def action_shortlist(self):
        """Mark candidate as shortlisted."""
        self.write({'state': 'shortlisted'})

    def action_reject(self):
        """Mark candidate as rejected."""
        self.write({'state': 'rejected'})

    def action_reset_draft(self):
        """Reset to draft state."""
        self.write({
            'state': 'draft',
            'analysis_error': False,
            'overall_score': 0,
            'hiring_recommendation': False,
        })
