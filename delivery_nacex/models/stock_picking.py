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
    bultos = fields.Integer('Bultos')
    picking_contenedor= fields.Many2one('stock.picking', 'Albarán contenedor')
    
    def send_to_shipper(self):
        if not self.env.context.get("force_send_to_shipper") and self.carrier_id.delivery_type == 'nacex' and self.state != "assigned":
            return
        return super(Picking, self).send_to_shipper()
    
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
    
    def obtener_etiqueta(self):
        nacex = NacexRequest(self.log_xml)
        for r in self:
            if r.carrier_tracking_ref:
                fichero_etiqueta = nacex.get_label(r.carrier_tracking_ref, r.nacex_etiqueta, self)
                cb_picking_zpl = "^XA^XFETIQUETA^FS^FO475,770^BY2,1^BCB,100,Y,N,N^FD" + r.name + "^FS"
                etiqueta = fichero_etiqueta.replace("^DFETIQUETA", "^CI28^DFETIQUETA").replace("^XA^XFETIQUETA^FS", cb_picking_zpl)
                r.etiqueta_envio_zpl = etiqueta
        
