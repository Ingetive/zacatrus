# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_barcode = fields.Char(related='product_id.barcode', string = "Código de barras")
    
    @api.model
    def create(self, vals):
        if vals.get('picking_id') and vals.get('picking_type_id'):
            order_line = self.env['sale.order.line'].sudo().search([
                ('id', '=', vals.get('sale_line_id')),
                ('order_id.amazon_order_ref', '!=', False)
            ], limit=1)
            
            if order_line:
                picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
                if picking_type.id == 3:
                    vals.update({
                        'location_id': 93,
                        'location_dest_id': 14
                    })
                elif picking_type.id == 5:
                    vals.update({
                        'location_id': 14,
                        'location_dest_id': 9
                    })
        
        
        return super().create(vals)