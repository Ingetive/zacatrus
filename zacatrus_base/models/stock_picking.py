# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from .notifier import Notifier

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'
    #x_sync_status = fields.Integer(default=0)

    def setPartnerCarrier(self):
        # TODO: Migración => Revisar con datos como funcionaria la acción automatizada
        for picking in self:
            if not picking.picking_type_id.id == 5 or not picking.partner_id or not picking.partner_id.property_delivery_carrier_id:
                return False
            if not picking.partner_id or not picking.partner_id.property_delivery_carrier_id:
                return False

            newCarrierId = picking.partner_id.property_delivery_carrier_id.id
            # If valija
            if newCarrierId == 9:
                if picking.origin.endswith("-DHL"):
                    newCarrierId = 14 # DHL Carry

            picking.write({'carrier_id' : newCarrierId})

    def send_to_shipper(self):
        # TODO: Migración => Metodo nuevo posterior a refactorizacion para V16
        if self.carrier_id.id == 13 and self.number_of_packages > 1:
            _logger.info(f"Zacalog: send_to_shipper")
            self.write({
                'carrier_id': 15,
            })

        return super(Picking, self).send_to_shipper()

    def get_label_dhl_txt(self):
        if self.carrier_id.delivery_type == 'dhl_parcel':
            attach = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'stock.picking'),
                ('res_id', '=', self.id),
                ('index_content', '!=', False),
                ('mimetype', '=', 'text/plain'),
                ('type', '=', 'binary')
            ], order="create_date desc", limit=1)
            if attach:
                return attach.index_content
        return None