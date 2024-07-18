{
    "name": "Zacatrus EDI",
    "version": "16.0.0.0.1",
    "category": "Sales",
    "summary": "EDI reports",
    'author': "Zacatrus",
    'website': "https://zacatrus.es",
    "license": "AGPL-3",
    "depends": [
        'base',
        'sale'
    ],
    "data": [
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
        'report/zacaedi_views.xml',
        'report/zacatrus_edi_delivery_label.xml',
        'report/zacatrus_edi_external_layout.xml',
    ],
    "installable": True,
}
