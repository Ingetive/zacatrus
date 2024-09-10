{
    "name": "POS Aplazame Payment",
    "version": "16.0.0.0.1",
    "category": "Point Of Sale",
    "summary": "Point of sale: supports Aplazame payment",
    'author': "Zacatrus",
    'website': "https://zacatrus.es",
    "license": "AGPL-3",
    'depends': [
        "point_of_sale",
    ],
    "data": [
        # "views/assets.xml", # TODO: Migración => Evaluar en OWL esta personalización
        'views/pos_config.xml',
        'views/res_config_settings_views.xml',
        'data/ir_action_data.xml',
    ],
    "installable": True,
}
