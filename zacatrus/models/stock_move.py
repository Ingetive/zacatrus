# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_barcode = fields.Char(related='product_id.barcode', string = "Código de barras")