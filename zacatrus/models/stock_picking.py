# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_tracking = fields.Char("Numero de tracking de la mensajeria")
    x_status = fields.Integer('Estado de sincronización')
    partner_zip = fields.Char(related="partner_id.zip", store=True)

    def _check_immediate(self):
        """ Inherit stock/models/stock_picking """
        immediate_pickings = self.browse()
        # DHL B2B a DHL Carry para que obligue a pedir bultos en Segovia
        for picking in self:
            if picking['carrier_id'].id == 14 and picking.picking_type_id.id == 5:
                immediate_pickings |= picking
            else:
                immediate_pickings = super(StockPicking, self)._check_immediate()

        return immediate_pickings
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('origin'):
                defaults = self.default_get(['name', 'picking_type_id'])
                domain_order =  [('name', '=', vals.get('origin')), ('amazon_order_ref', '!=', False)]
                order = self.env['sale.order'].sudo().search(domain_order, limit=1)

                if order:
                    picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
                    if picking_type.id == 3:
                        vals.update({'location_id': 936, 'location_dest_id': 14})
                    elif picking_type.id == 5:
                        vals.update({'location_id': 14, 'location_dest_id': 9})
                    
        return super().create(vals_list)
