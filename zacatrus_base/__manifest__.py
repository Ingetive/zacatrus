{
    "name": "Zacatrus Base",
    "version": "16.0.0.0.2",
    "category": "Point Of Sale",
    "summary": "Base settings for Zacatrus modules",
    'author': "Zacatrus",
    'website': "https://zacatrus.es",
    "license": "AGPL-3",
    "depends": [
        'account',
        'base',
        'point_of_sale',
        'product',
        'purchase',
        'sale',
        #'zacatrus',
        #'delivery_dhl_parcel'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'report/report_deliveryslip_ticket.xml',
        'report/zacatrus_base_views.xml',
        'report/stock_picking.xml',
        'report/report_delivery_document.xml',
        'data/mail_template.xml',
        'data/ir_action_data.xml'
    ],
    "installable": True,
    'assets': {
        'point_of_sale.assets': [
            'zacatrus_base/static/src/xml/zaca_order_receipt.xml',
        ],
    },
}
