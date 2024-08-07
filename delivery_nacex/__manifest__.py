# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>
{
    'name': "Envíos Nacex",
    'description': "Envíe sus envíos a través de Nacex y realice un seguimiento en línea",
    'category': 'Inventory/Delivery',
    'author': "Voodoo",
    'website': "https://www.voodoo.es",
    'sequence': 1,
    'version': '1.0',
    'application': True,
    'depends': [
        'delivery',
        'mail',
        # 'printnode_base', # TODO: Migración => Falta adquirir este modulo
    ],
    'data': [
        'data/delivery_nacex.xml',
        'security/ir.model.access.csv',
        'views/delivery_nacex.xml',
        'views/res_config_settings.xml',
        'views/stock_picking.xml',
        'wizard/envio_nacex_valija.xml',
        'report/nacex_templates.xml',
        'report/nacex_reports.xml',
    ],
    'installable': True,
    'license': 'Other proprietary',
}