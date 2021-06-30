# -*- coding: utf-8 -*-
{
    'name': "zacasocios",

    'summary': """
        Permite gestionar Zacasocios """,

    'description': """
        Asigna y permite redimir Fichas
    """,

    'author': "Zacatrus",
    'website': "https://zacatrus.es",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/Fichas.xml',
        'static/src/xml/Tarjezaca.xml',
    ],
    'installable': True,
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}