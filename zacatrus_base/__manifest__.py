{
    "name": "Zacatrus Base",
    "version": "14.0.2.0.0",
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
        'sale'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    "installable": True,
}
