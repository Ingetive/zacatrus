# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        
        if res.order_id.team_id.id == 14 and res.product_id.id != self.env.ref("sale_amazon.shipping_product").id: # Equipo de venta -> Amazon
            res.write({'route_id': 58}) # Ruta -> Segovia: Entregar en 2 pasos (Empaquetado + Enviar) Amazon
        
        return res