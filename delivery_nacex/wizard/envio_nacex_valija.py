# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

from odoo import api, fields, models

class EnvioValija(models.TransientModel):
    _name = 'delivery_nacex.envio_valija'
    _description = 'Nacex envio Valija'
    
    bultos = fields.Integer('Bultos')

    def action_envio_nacex_valija_apply(self):
        #crear envio
        
        #imprimir etiqueta de envio
        
        #actualizar seguimiento
        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        for albaran in pickings:
            albaran.carrier_tracking_ref = 'FELIX'
    