# -*- coding: utf-8 -*-
{
    'name': "zacatrus",

    'summary': """
        Personalizaciones Zacatrus
     """,

    'description': """
        Módulo creado para dar soporte a las modificaciones
        realizadas directamente en base de datos en las versiones anteriores
    """,

    'author': "Voodoo",
    'website': "http://www.voodoo.es",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0',

    # any module necessary for this one to work correctly
    'depends': [
        'account',
        'base',
        'point_of_sale',
        'product',
        'purchase',
        'sale',
        'stock_barcode',
        'stock_account',
        'delivery_nacex'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/purchase.xml',
        'views/views.xml',
        'views/point_of_sale.xml',
        'views/account_move.xml',
        'views/stock_picking.xml',
        'views/stock_valuation_layer.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'report/etiqueta_vit.xml',
        'report/zacatrus_views.xml',
        'report/report_delivery_document.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
