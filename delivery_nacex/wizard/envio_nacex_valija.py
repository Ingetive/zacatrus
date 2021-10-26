# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

from odoo import api, fields, models

class EnvioValija(models.TransientModel):
    _name = 'delivery_nacex.envio_valija'
    _description = 'Nacex envio Valija'

    bultos = fields.Integer('Bultos')

    def action_envio_nacex_valija_apply(self):
        #verificar que todos los pickings tengan la misma direccion de entrega
        nacex = self.env['delivery.carrier'].search([('delivery_type','=','nacex')])
        picking_contenedor = False
        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        for albaran in pickings:
            albaran.bultos = self.bultos
            if not contenedor:
                picking_contenedor = albaran.name
                nacex.nacex_send_shipping(albaran)                
            else:
                albaran.picking_contenedor = picking_contenedor
