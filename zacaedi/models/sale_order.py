# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    x_edi_order = fields.Char(readonly=False)
    x_edi_shipment = fields.Char(readonly=False)