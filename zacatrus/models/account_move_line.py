# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    product_barcode = fields.Char(related='product_id.barcode', string="Código de barras")