# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging
import requests
import base64

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'
    
    etiqueta_envio_zpl = fields.Text("Etiqueta envio ZPL")

    def imprimir_operacion(self):
        nacex_id = self.env.ref('delivery_nacex.delivery_carrier_nacex').id
        nacex_valija_id = self.env.ref('delivery_nacex.delivery_carrier_nacex_valija').id
        if self.carrier_id.id == nacex_id:
            #imprimir etiqueta
            return self.env.ref('delivery_nacex.report_nacex_label').report_action(self)
        elif self.carrier_id.id == nacex_valija_id:
            #imprimir albaran
            return self.env.ref('stock.action_report_picking').report_action(self)            

