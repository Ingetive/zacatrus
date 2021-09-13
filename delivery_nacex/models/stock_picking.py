# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'
    
    etiqueta_envio_zpl = fields.Text("Etiqueta envio ZPL")

    def send_to_shipper(self):
        res = super(Picking, self).send_to_shipper()
        #if self.carrier_id.delivery_type == "nacex":
        #    return self.print_etiqueta()
        return res
    
    def button_validate(self):
        res = super(Picking, self).button_validate()
        #if res is True:
        #    for picking in self:
        #        if picking.carrier_id.delivery_type == "nacex":
        #            return picking.print_etiqueta()
        #        
        #    for picking in self:
        #        if picking.location_id.usage == 'internal' and picking.location_dest_id.usage == 'internal':
        #            return picking.action_report_relacion_operaciones()
        return res
    
    def print_etiqueta(self):
        try:
            return self.env.ref('delivery_nacex.report_nacex_label').report_action(self.id)
        except:
            _logger.error("Se intento imprimir la etiqueta de Nacex pero se produjo un error.")
            
    def action_report_relacion_operaciones(self):
        try:
            return self.env.ref('delivery_nacex.report_relacion_operaciones').report_action(self.id)
        except:
            _logger.error("Se intento imprimir la etiqueta de Nacex pero se produjo un error.")
