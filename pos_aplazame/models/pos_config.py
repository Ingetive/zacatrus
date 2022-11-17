# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_aplazame_key = fields.Char("Aplazame private api key")
    x_shop_code = fields.Char("Código de tienda Zacatrus")
    x_min_amount = fields.Integer("Importe mínimo del pedido para financiar")