# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'
    
    etiqueta_envio_zpl = fields.Text("Etiqueta envio ZPL")

    def send_to_shipper(self):
        super(Picking, self).send_to_shipper()
        if self.carrier_id.delivery_type == "nacex":
            return self.print_etiqueta()
    
    def button_validate(self):
        res = super(Picking, self).button_validate()
        if res is True and self.carrier_id.delivery_type == "nacex":
            try:
                return self.print_etiqueta()
            except:
                _logger.error("Se intento imprimir la etiqueta de Nacex pero se produjo un error.")
        return res
    
    def print_etiqueta(self):
        return self.env.ref('delivery_nacex.report_nacex_label').report_action(self.id)
