# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class PosConfig(models.Model):
    _inherit = 'pos.config'

    #x_paylands_key = fields.Char("Paylands api key")
    x_paylands_device = fields.Char("Código de dispositivo")
    #x_min_amount = fields.Integer("Importe mínimo del pedido para financiar")