# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_edi_line = fields.Char(readonly=False)
    x_edi_product = fields.Char(readonly=False)

    def create(self, vals):
        order = self.env['sale.order'].browse(vals['order_id'])
        if order.x_edi_order and not self.env.uid == 1:
            raise UserError('No se pueden añadir líneas a un pedido que viene por EDI.')
        return super(SaleOrderLine, self).create(vals)