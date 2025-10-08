{
    "name": "Zacatrus EDI",
    "version": "18.0.0.0.1",
    "category": "Sales",
    "summary": "EDI connector and labels",
    'author': "Zacatrus",
    'website': "https://zacatrus.es",
    "license": "AGPL-3",
    "depends": [
        'base',
        'sale_management',
        'stock'
    ],
    "data": [
        'views/res_config_settings_views.xml',
        'views/sale_order.xml',
        'security/ir.model.access.csv',
        'report/zacatrus_edi_delivery_label.xml',
        'report/zacatrus_edi_external_layout.xml',
        'data/ir_action_data.xml',
        'report/zacaedi_views.xml',
    ],
    "installable": True,
    'external_dependencies': {
        'python': ['barcode'],
    },
}
