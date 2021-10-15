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
        #En el escenario es donde, según el dominio, imprimiremos el report:
        # - etiqueta Nacex ZPL (Método de envío Nacex) 
        # - Operaciones albarán (Método de envío Nacex valija)
        printed = self.print_scenarios(action='print_document_on_transfer')
        if printed:
            self.write({'printed': True})       
        
    def action_show_envio_nacex_valija_wizard(self):
        view = self.env.ref('view_envio_nacex_valija_wizard')
        action = {
                    'name': _('Crear envio Nacex valija'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'delivery_nacex.envio_nacex_valija',
                    'views': [(view.id, 'form')],
                    'target': 'new',
                    'res_id': self.id,
                }
        return action
