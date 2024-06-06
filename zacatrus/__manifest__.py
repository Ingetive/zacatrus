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
    'category': 'Uncategorized',
    'version': '16.0',
    'depends': [
        'account',
        'base',
        'point_of_sale',
        'product',
        'purchase',
        'sale',
        'stock_barcode',
        'stock_account',
        'delivery_nacex',
        'stock', 
        # 'stock_location_children', TODO: Migración => No se migra por que V16 ya tiene un campo para los child_ids
        'sale_amazon',
        'portal',
        'account_fiscal_position_partner_type'
    ],
    'data': [
        'security/point_of_sale.xml',
        'security/ir.model.access.csv',
        'report/purchase.xml',
        'views/views.xml',
        'views/point_of_sale.xml',
        'views/account_move.xml',
        'views/stock_picking.xml',
        'views/stock_valuation_layer.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/stock_batch_picking_view.xml',
        'report/etiqueta_vit.xml',
        'report/zacatrus_views.xml',
        'report/report_delivery_document.xml',
        # 'views/templates.xml', TODO: Migración => Evaluar si estilos de PdV en V16 son suficientes
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'zacatrus/static/src/models/lazy_barcode_cache.js',
        ],
        'point_of_sale.assets': [
            'zacatrus/static/src/js/Chrome.js',
        ],
    },
}