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
        # "views/assets.xml", # TODO: Migración => Evaluar en OWL esta personalización
    ],
    "installable": True,
    'assets': {
       'point_of_sale.assets': [
           'pos_tarjezaca/static/src/js/payment_terminal.js',
           'pos_tarjezaca/static/src/js/models.js',
       ],
    },
}
