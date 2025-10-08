{
    'name': 'Zacatrus Amazon',
    "version": "18.0.0.0.1",
    'depends': ['sale_amazon'],  # ou 'contacts' si tu travailles sur res.partner
    'author': 'Zacatrus',
    'category': 'Customization',
    "summary": "Module to customize Amazon for Zacatrus.",
    'description': '''Module to customize Amazon for Zacatrus.
        This module is proprietary software.
        All rights reserved.
        Reproduction, distribution, or modification without written permission is strictly prohibited.
    ''',
    'website': "https://zacatrus.es",
    'data': [],
    'installable': True,
    'license': 'Other proprietary',
    'data': [
        'views/amazon_account_inherit.xml',
        'views/stock_picking_inherit.xml',
    ],
}