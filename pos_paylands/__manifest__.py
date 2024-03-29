{
    "name": "POS Paylands Payment",
    "version": "14.0.1.0.0",
    "category": "Point Of Sale",
    "summary": "Point of sale: supports Paylands payment",
    'author': "Zacatrus",
    'website': "https://zacatrus.es",
    "license": "AGPL-3",
    'depends': [
        "point_of_sale",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/assets.xml",
        'views/pos_config.xml',
        'views/res_config_settings_views.xml',
    ],
    "installable": True,
}
