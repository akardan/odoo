# -*- coding: utf-8 -*-
{
    'name': 'Form Full Screen | Form Full Width | Chatter Toggle Position | Hide Chatter',
    'version': '18.0.0.0.0',
    'summary': 'Enhance Odoo form view: Full Screen/Width, Chatter Toggle (Side/Bottom), Hide Chatter, Improved UX for Large Screens',
    'description': """
        The Form Full Screen/Width & Chatter Toggle module enhances the Odoo form view experience, especially on large screens. It provides the following features:
        
        - Toggle the position of the chatter (messages & activities) to the side of the form view for better usability on wide monitors.
        - Instantly hide or show the chatter panel to maximize workspace and focus on form content.
        - Enable full-width (full screen) mode for form views, removing default width restrictions for a more immersive editing experience.
        - Smooth, animated toggle button integrated into the form status bar for easy access.
        - No configuration required: install and use immediately.
        - Clean, modern UI with subtle animations for a professional look.
        
        This module is ideal for users who work extensively with form views and want a more flexible, distraction-free interface in Odoo 18.0.
        
        Support: prt.c.bhatti@gmail.com
    """,
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'form_full_screen/static/src/**/*',
        ],
    },
    'maintainer': 'Preet',
    'support': 'prt.c.bhatti@gmail.com',
    'category': 'User Interface',
    'author': "Preet Bhatti",
    'website': "https://preetbhatti.github.io/portfolio/",
    'license': 'OPL-1',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
} 