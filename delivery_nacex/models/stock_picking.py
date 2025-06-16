# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging
import requests
import base64
import re

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from .nacex_request import NacexRequest

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'
    
    etiqueta_envio_zpl = fields.Text("Etiqueta envio ZPL")
    x_tracking = fields.Char("Numero de tracking de la mensajeria", compute='_compute_tracking')
    bultos = fields.Integer('Bultos')
    picking_contenedor = fields.Many2one('stock.picking', 'Albarán contenedor')
    codigo_expedicion = fields.Char("Código Expedición")
    x_tracking_nx = fields.Char("Tracking NX de la mensajeria", compute='_compute_tracking_nx')

    @api.depends('etiqueta_envio_zpl')
    def _compute_tracking(self):
        for r in self:
            try:
                r.x_tracking = re.search('[0-9]{4}\\/[0-9]{8}', r.etiqueta_envio_zpl).group(0)
            except:
                r.x_tracking = False

    @api.depends('etiqueta_envio_zpl')
    def _compute_tracking_nx(self):
        for r in self:
            try:
                r.x_tracking_nx = re.search(r'\^FD(NX[^\^]+)\^', r.etiqueta_envio_zpl).group(1)
            except:
                r.x_tracking_nx = False
    
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
    
    def obtener_etiqueta_nacex(self, codigo_expedicion=None):
        for r in self.sudo():
            if r.carrier_id.delivery_type != "nacex":
                continue
                
            if not codigo_expedicion:
                codigo_expedicion = r.codigo_expedicion
            
            if not codigo_expedicion:
                continue
            
            nacex = NacexRequest(r.carrier_id.log_xml)
            fichero_etiqueta = nacex.get_label(codigo_expedicion, r.carrier_id.nacex_etiqueta, r.carrier_id)
            if not fichero_etiqueta:
                raise ValidationError("No se ha podido obtener la etiqueta desde Nacex.")
            cb_picking_zpl = "^XA^XFETIQUETA^FS^FO475,770^BY2,1^BCB,100,Y,N,N^FD" + r.name + "^FS"
            etiqueta = fichero_etiqueta.replace("^DFETIQUETA", "^CI28^DFETIQUETA").replace("^XA^XFETIQUETA^FS", cb_picking_zpl)
            r.etiqueta_envio_zpl = etiqueta
        
