# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrderLine, self).create(vals_list)
        for record in res:
            if record.order_id.team_id.id == 14 and record.product_id.id != self.env.ref("sale_amazon.shipping_product").id:  # Equipo de venta -> Amazon
                record.write({'route_id': 58})  # Ruta -> Segovia: Entregar en 2 pasos (Empaquetado + Enviar) Amazon
        return res
