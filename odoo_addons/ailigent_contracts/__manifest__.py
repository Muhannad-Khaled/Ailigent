{
    'name': 'Ailigent Contracts',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'AI-Powered Contract Analysis and Management',
    'description': """
        Ailigent Contracts Module
        =========================

        This module provides AI-powered contract analysis capabilities:

        Features:
        ---------
        * Contract text extraction and analysis
        * AI-powered clause identification
        * Risk assessment and scoring
        * Key dates and obligations tracking
        * Compliance recommendations
        * Integration with external AI service (FastAPI backend)

        Configuration:
        --------------
        Go to Settings > Ailigent > Contracts to configure the API connection.
    """,
    'author': 'Ailigent',
    'website': 'https://ailigent.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_analysis_views.xml',
        'views/contract_settings_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Add JS/CSS assets here if needed
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
