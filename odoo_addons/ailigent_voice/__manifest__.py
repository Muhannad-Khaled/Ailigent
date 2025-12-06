{
    'name': 'Ailigent Voice',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'AI Voice Assistant Configuration and Session Management',
    'description': """
        Ailigent Voice Module
        =====================

        This module provides configuration and session management for the
        AI Voice Assistant powered by LiveKit:

        Features:
        ---------
        * Voice assistant language preferences
        * Voice persona configuration
        * Session history with transcripts
        * Integration with external voice service (FastAPI + LiveKit)

        Configuration:
        --------------
        Go to Settings > Ailigent > Voice to configure the service connection.
    """,
    'author': 'Ailigent',
    'website': 'https://ailigent.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'mail',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/voice_settings_views.xml',
        'views/voice_session_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
