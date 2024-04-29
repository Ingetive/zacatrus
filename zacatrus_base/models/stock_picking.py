# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'

    def setPartnerCarrier(self):
        # Solo para el tipo de operación 'Segovia: Órdenes de entrega' (id 5)
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

            picking.write({
              'carrier_id' : newCarrierId
            })

    def send_to_shipper(self):
        if self.carrier_id.id == 13 and self.number_of_packages > 1:
            _logger.info(f"Zacalog: send_to_shipper")
            self.write({
                'carrier_id' : 15,
            })
            
        return super(Picking, self).send_to_shipper()