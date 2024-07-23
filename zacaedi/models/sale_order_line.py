# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_edi_line = fields.Char(readonly=False)
    x_edi_product = fields.Char(readonly=False)