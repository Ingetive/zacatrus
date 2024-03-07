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
    'category': 'Uncategorized',
    'version': '16.0',
    'depends': [
        "zacatrus_base", 
        'point_of_sale'
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    # 'qweb': [
    #     'static/src/xml/Fichas.xml', # TODO: Migración => Evaluar en OWL esta personalización
    # ],
    'installable': True,
}