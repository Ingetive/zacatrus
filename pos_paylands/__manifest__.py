{
    "name": "POS Paylands Payment",
    "version": "16.0.0.0.1",
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
        # "views/assets.xml", # TODO: Migración => Evaluar en OWL esta personalización
        'views/pos_config.xml',
        'views/res_config_settings_views.xml',
    ],
    "installable": True,
    'assets': {
       'point_of_sale.assets': [
           'pos_paylands/views/pos_config.xml',
           'pos_paylands/static/src/js/payment_terminal.js',
           'pos_paylands/static/src/js/models.js',
       ],
    },
}
