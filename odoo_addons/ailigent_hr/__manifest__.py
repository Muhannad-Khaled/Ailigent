{
    'name': 'Ailigent HR',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'AI-Powered HR Analytics and Recruitment',
    'description': """
        Ailigent HR Module
        ==================

        This module provides AI-powered HR capabilities:

        Features:
        ---------
        * CV Analysis with AI scoring
        * Candidate ranking and comparison
        * Appraisal summary generation
        * HR insights and analytics
        * Attendance anomaly detection
        * Interview question generation
        * Integration with external AI service (FastAPI backend)

        Configuration:
        --------------
        Go to Settings > Ailigent > HR to configure the API connection.
    """,
    'author': 'Ailigent',
    'website': 'https://ailigent.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'hr_recruitment',
        'mail',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cv_analysis_views.xml',
        'views/hr_insights_views.xml',
        'views/hr_settings_views.xml',
        'views/menu.xml',
        'wizards/cv_upload_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
