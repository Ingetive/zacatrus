# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class PosPaylandsPayment(models.Model):
    _name = 'pos_paylands.payment'
    _description = 'Paylands payments'

    #x_paylands_key = fields.Char("Paylands api key")
    order_id = fields.Char("Id del pedido")
    status = fields.Integer("Estado del pedido")
    amount = fields.Integer("Importe total")
    #x_min_amount = fields.Integer("Importe mínimo del pedido para financiar")