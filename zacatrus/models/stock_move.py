# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_barcode = fields.Char(related='product_id.barcode', string = "Código de barras")
    
    @api.model
    def create(self, vals):
        _logger.warning("create")
        _logger.warning(vals)
        
        res = super().create(vals)
        
        _logger.warning("despues de create")
        _logger.warning(res.id)
        _logger.warning(res.location_id)
        
        return res
        
        
    
    def write(self, vals):
        _logger.warning("write")
        _logger.warning(self.ids)
        _logger.warning(vals)
        res = super().write(vals)
        
        return res
