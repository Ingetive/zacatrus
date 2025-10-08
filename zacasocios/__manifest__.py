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
    "license": "AGPL-3",
    'category': 'Uncategorized',
    'version': '18.0',
    'depends': [
        'point_of_sale'
    ],
    'data': [
        'views/res_config_settings_views.xml',
        'data/ir_action_data.xml',
        'security/ir.model.access.csv',
        'report/zacasocios_views.xml',
    ],
    #'qweb': [
    #     'static/src/xml/Fichas.xml', # TODO: Migración => Evaluar en OWL esta personalización
    #],
    'installable': True,
    'license': 'Other proprietary',
    'assets': {
        'point_of_sale._assets_pos': [
            'zacasocios/static/src/js/fichas_button_patch.js',
        ],
    },
}