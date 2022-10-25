# -*- coding: utf-8 -*-

{
    'name': 'Pos Open Cash Drawer',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Allows you to open cash drawer from product screen.',
    'description': """

=======================

Allows you to open cash drawer from product screen.

""",
    'depends': ['point_of_sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/pos.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 12,
    'currency': 'USD',
}
