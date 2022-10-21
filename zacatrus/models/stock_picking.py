# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'

    x_tracking = fields.Char("Numero de tracking de la mensajeria")
    x_status = fields.Integer('Estado de sincronización')
    partner_zip = fields.Char(related="partner_id.zip", store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('origin'):
            defaults = self.default_get(['name', 'picking_type_id'])
            order = self.env['sale.order'].sudo().search([
                ('name', '=', vals.get('origin')),
                ('amazon_order_ref', '!=', False)
            ], limit=1)
            
            if order:
                picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
                if picking_type.id == 3:
                    vals.update({
                        'location_id': 936,
                        'location_dest_id': 14
                    })
                elif picking_type.id == 5:
                    vals.update({
                        'location_id': 14,
                        'location_dest_id': 9
                    })
                    
        return super().create(vals)
