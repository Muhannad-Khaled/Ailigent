"""CV Upload Wizard - Bulk upload and analysis."""

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class CVUploadWizard(models.TransientModel):
    """Wizard for bulk CV upload and analysis."""

    _name = 'ailigent.cv.upload.wizard'
    _description = 'CV Upload Wizard'

    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        required=True,
    )
    cv_files = fields.Many2many(
        'ir.attachment',
        string='CV Files',
        help='Upload multiple CV files (PDF, DOCX)',
    )
    auto_analyze = fields.Boolean(
        string='Auto-Analyze',
        default=True,
        help='Automatically trigger AI analysis after upload',
    )

    def action_upload(self):
        """Process uploaded CV files."""
        self.ensure_one()

        if not self.cv_files:
            raise UserError('Please upload at least one CV file.')

        CVAnalysis = self.env['ailigent.cv.analysis']
        created_analyses = []

        for attachment in self.cv_files:
            # Extract candidate name from filename
            filename = attachment.name or 'Unknown'
            candidate_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')

            # Create CV analysis record
            analysis = CVAnalysis.create({
                'name': candidate_name,
                'job_id': self.job_id.id,
                'cv_file': attachment.datas,
                'cv_filename': attachment.name,
            })
            created_analyses.append(analysis.id)

            # Auto-analyze if enabled
            if self.auto_analyze:
                try:
                    analysis.action_analyze()
                except Exception as e:
                    _logger.warning(f"Auto-analysis failed for {candidate_name}: {e}")

        # Return action to view created analyses
        return {
            'type': 'ir.actions.act_window',
            'name': 'Uploaded CV Analyses',
            'res_model': 'ailigent.cv.analysis',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_analyses)],
            'target': 'current',
        }
