"""Workload Snapshot Model - Team workload analysis."""

from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class WorkloadSnapshot(models.Model):
    """Model to store team workload snapshots and AI analysis."""

    _name = 'ailigent.workload.snapshot'
    _description = 'Team Workload Snapshot'
    _order = 'create_date desc'

    name = fields.Char(
        string='Snapshot Name',
        required=True,
        default=lambda self: f"Workload Analysis - {fields.Datetime.now()}",
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('analyzing', 'Analyzing'),
        ('analyzed', 'Analyzed'),
        ('error', 'Error'),
    ], string='Status', default='draft')

    # Filters
    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
        help='Leave empty for all projects',
    )
    department_ids = fields.Many2many(
        'hr.department',
        string='Departments',
        help='Leave empty for all departments',
    )

    # AI Analysis Results
    balance_score = fields.Float(
        string='Balance Score',
        readonly=True,
        help='Team workload balance score (0-100)',
    )
    summary = fields.Text(string='AI Summary', readonly=True)

    # Structured Data (JSON)
    overloaded_data = fields.Text(string='Overloaded Employees (JSON)', readonly=True)
    underutilized_data = fields.Text(string='Underutilized Employees (JSON)', readonly=True)
    deadline_risks_data = fields.Text(string='Deadline Risks (JSON)', readonly=True)
    recommendations_data = fields.Text(string='Recommendations (JSON)', readonly=True)

    # Display Fields
    overloaded_display = fields.Html(string='Overloaded', compute='_compute_overloaded_display')
    underutilized_display = fields.Html(string='Underutilized', compute='_compute_underutilized_display')
    recommendations_display = fields.Html(string='Recommendations', compute='_compute_recommendations_display')

    analysis_error = fields.Text(string='Error', readonly=True)
    analyzed_at = fields.Datetime(string='Analyzed At', readonly=True)

    @api.depends('overloaded_data')
    def _compute_overloaded_display(self):
        import json
        for record in self:
            if record.overloaded_data:
                try:
                    employees = json.loads(record.overloaded_data)
                    html = '<table class="table table-sm"><thead><tr><th>Employee</th><th>Utilization</th><th>Recommendation</th></tr></thead><tbody>'
                    for emp in employees:
                        util = emp.get('utilization', 0)
                        badge = 'danger' if util > 100 else 'warning'
                        html += f"<tr><td>{emp.get('name', 'N/A')}</td>"
                        html += f"<td><span class='badge bg-{badge}'>{util:.0f}%</span></td>"
                        html += f"<td>{emp.get('recommendation', 'N/A')}</td></tr>"
                    html += '</tbody></table>'
                    record.overloaded_display = html
                except Exception:
                    record.overloaded_display = '<p>Unable to parse</p>'
            else:
                record.overloaded_display = '<p class="text-success">No overloaded employees</p>'

    @api.depends('underutilized_data')
    def _compute_underutilized_display(self):
        import json
        for record in self:
            if record.underutilized_data:
                try:
                    employees = json.loads(record.underutilized_data)
                    html = '<table class="table table-sm"><thead><tr><th>Employee</th><th>Utilization</th><th>Recommendation</th></tr></thead><tbody>'
                    for emp in employees:
                        util = emp.get('utilization', 0)
                        html += f"<tr><td>{emp.get('name', 'N/A')}</td>"
                        html += f"<td><span class='badge bg-info'>{util:.0f}%</span></td>"
                        html += f"<td>{emp.get('recommendation', 'N/A')}</td></tr>"
                    html += '</tbody></table>'
                    record.underutilized_display = html
                except Exception:
                    record.underutilized_display = '<p>Unable to parse</p>'
            else:
                record.underutilized_display = '<p>No underutilized employees</p>'

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

    def action_analyze(self):
        """Trigger workload analysis."""
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

            # Gather employee and task data
            employees_data = self._gather_employee_data()
            tasks_data = self._gather_task_data()

            payload = {
                'employees': employees_data,
                'tasks': tasks_data,
                'weekly_capacity': 40.0,
            }

            url = f"{settings.api_url.rstrip('/')}/api/v1/distribution/analyze-workload"
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
            _logger.error(f"Workload analysis error: {e}")
            self.write({
                'state': 'error',
                'analysis_error': str(e),
            })

        return True

    def _gather_employee_data(self):
        """Gather employee data for analysis."""
        Employee = self.env['hr.employee']
        Task = self.env['project.task']

        domain = []
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))

        employees = Employee.search(domain)
        result = []

        for emp in employees:
            # Count active tasks
            task_domain = [('user_ids', 'in', [emp.user_id.id])] if emp.user_id else []
            if self.project_ids:
                task_domain.append(('project_id', 'in', self.project_ids.ids))
            task_domain.append(('stage_id.fold', '=', False))

            tasks = Task.search(task_domain)

            result.append({
                'id': emp.id,
                'name': emp.name,
                'department': emp.department_id.name if emp.department_id else 'Unassigned',
                'active_tasks': len(tasks),
                'total_hours_assigned': sum(t.planned_hours or 0 for t in tasks),
            })

        return result

    def _gather_task_data(self):
        """Gather task data for analysis."""
        Task = self.env['project.task']

        domain = [('stage_id.fold', '=', False)]
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))

        tasks = Task.search(domain, limit=500)
        result = []

        for task in tasks:
            result.append({
                'id': task.id,
                'name': task.name,
                'project': task.project_id.name if task.project_id else 'No Project',
                'assignee': task.user_ids[0].name if task.user_ids else 'Unassigned',
                'priority': task.priority or '0',
                'deadline': str(task.date_deadline) if task.date_deadline else None,
                'planned_hours': task.planned_hours or 0,
            })

        return result

    def _process_analysis_result(self, result):
        """Process the analysis result."""
        import json
        from datetime import datetime

        analysis = result.get('analysis', result)

        vals = {
            'state': 'analyzed',
            'analyzed_at': datetime.now(),
            'balance_score': analysis.get('balance_score', 0),
            'summary': analysis.get('summary', ''),
        }

        if analysis.get('overloaded_employees'):
            vals['overloaded_data'] = json.dumps(analysis['overloaded_employees'])
        if analysis.get('underutilized_employees'):
            vals['underutilized_data'] = json.dumps(analysis['underutilized_employees'])
        if analysis.get('deadline_risks'):
            vals['deadline_risks_data'] = json.dumps(analysis['deadline_risks'])
        if analysis.get('recommendations'):
            vals['recommendations_data'] = json.dumps(analysis['recommendations'])

        self.write(vals)
