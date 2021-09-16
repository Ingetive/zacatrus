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

    def imprimir_etiqueta(self):
        action = self.env.ref('delivery_nacex.report_nacex_label').report_action(self.id)
        device = self.env['iot.device'].search([('identifier', '=', action['device_id'])], limit=1)
        etiqueta = bytes(self.etiqueta_envio_zpl, 'utf-8')
        
        self.env['bus.bus'].sudo().sendone(
            (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
            {
                'type': 'iot_print_documents',
                'documents': [base64.encodebytes(etiqueta)],
                'iot_device_identifier': action['device_id'],
                'iot_ip': device.iot_ip,
            }
        )


