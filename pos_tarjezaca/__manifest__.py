{
    "name": "POS Tarjezaca Payment",
    "version": "16.0.0.0.1",
    "category": "Point Of Sale",
    "summary": "Point of sale: support Tarjezaca payment",
    'author': "Zacatrus",
    'website': "https://zacatrus.es",
    "license": "AGPL-3",
    'depends': [
        "point_of_sale",
        "zacatrus_base"
    ],
    "data": [
        'views/res_config_settings_views.xml',
        'report/pos_tarjezaca_views.xml',
        'security/ir.model.access.csv',
        'data/ir_action_data.xml',
    ],
    "installable": True,
    'assets': {
       'point_of_sale.assets': [
           'pos_tarjezaca/static/src/js/payment_terminal.js',
           'pos_tarjezaca/static/src/js/models.js',
       ],
    }
}
