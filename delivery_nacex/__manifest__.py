# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>
{
    'name': "Envíos Nacex",
    'description': "Envíe sus envíos a través de Nacex y realice un seguimiento en línea",
    'category': 'Inventory/Delivery',
    'sequence': 275,
    'version': '1.0',
    'application': True,
    'depends': ['delivery', 'mail'],
    'data': [
        'data/delivery_nacex.xml',
        'views/delivery_nacex.xml',
        'views/res_config_settings.xml',
        'views/stock_picking.xml',
    ],
}
