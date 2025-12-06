{
    'name': 'Ailigent Tasks',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'AI-Powered Task Management and Workload Optimization',
    'description': """
        Ailigent Tasks Module
        =====================

        This module provides AI-powered task management capabilities:

        Features:
        ---------
        * Team workload visualization
        * AI task assignment recommendations
        * Bottleneck detection and alerts
        * Productivity reports and analytics
        * Integration with external AI service (FastAPI backend)

        Configuration:
        --------------
        Go to Settings > Ailigent > Tasks to configure the API connection.
    """,
    'author': 'Ailigent',
    'website': 'https://ailigent.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'hr',
        'mail',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/workload_views.xml',
        'views/bottleneck_views.xml',
        'views/task_settings_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
