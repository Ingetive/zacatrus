# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_barcode = fields.Char(related='product_id.barcode', string = "Código de barras")
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("sale_line_id"):
                domain_sale_line = [('id', '=', vals.get("sale_line_id")), ('order_id.amazon_order_ref', '!=', False)]
                sale_line = self.env['sale.order.line'].search(domain_sale_line, limit=1)
                if sale_line:
                    vals.update({"rule_id": 102, "route_ids": [(4, 58)]})
        
        _logger.warning("create")
        _logger.warning(vals_list)
        
        res = super().create(vals_list)

        return res
