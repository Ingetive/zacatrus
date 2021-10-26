# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

from odoo import api, fields, models

class EnvioValija(models.TransientModel):
    _name = 'delivery_nacex.envio_valija'
    _description = 'Nacex envio Valija'

    bultos = fields.Integer('Bultos', default=1)

    def action_envio_nacex_valija_apply(self):
        #TODO
        #Los albaranes tienen que estar en estado ready
        #Los albaranes tienen que tener metodo de transporte Nacex Valija
        #Los albaranes no tienen que tener Padre
        #Vista stock picking -> mostrar albaran contenedor solo si el metodo de envio es valija
        #Actualizar documento instrucciones
        nacex = self.env['delivery.carrier'].search([('delivery_type','=','nacex')])
        picking_contenedor = False
        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        for albaran in pickings:
            albaran.bultos = self.bultos
            if not picking_contenedor:
                picking_contenedor = albaran
                nacex.nacex_send_shipping(albaran)
                albaran.carrier_id = nacex
            else:
                albaran.picking_contenedor = picking_contenedor
