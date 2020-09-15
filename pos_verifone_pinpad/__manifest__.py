# -*- coding: utf-8 -*-
# © 2018 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2019 FactorLibre - Alvaro Rollan <alvaro.rollan@factorlibre.com>
{
    'name': 'PoS Verifone Pinpad',
    'version': '11.0.1.0.0',
    'depends': [
        'web',
        'point_of_sale',
    ],
    'category': 'Sales Management',
    'author': 'FactorLibre',
    'license': 'AGPL-3',
    'website': 'http://www.factorlibre.com',
    'data': [
        'templates/assets.xml',
        'views/pos_config_view.xml',
        'views/account_journal_view.xml'
    ],
    'qweb': ['static/src/xml/pos_verifone_pinpad.xml'],
    'installable': True,
    'application': False
}
