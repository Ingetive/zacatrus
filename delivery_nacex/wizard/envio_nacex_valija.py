# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

from odoo import api, fields, models
from odoo.exceptions import UserError

class EnvioValija(models.TransientModel):
    _name = 'delivery_nacex.envio_valija'
    _description = 'Nacex envio Valija'

    bultos = fields.Integer('Bultos', default=1)

    def action_envio_nacex_valija_apply(self):
        valija = self.env.ref('delivery_nacex.delivery_carrier_valija')
        nacex_valija = self.env.ref('delivery_nacex.delivery_carrier_nacex_valija')
        picking_contenedor = False
        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        for albaran in pickings:
            if not picking_contenedor:
                picking_contenedor = albaran
                picking_contenedor.bultos = self.bultos
                nacex_valija.nacex_send_shipping(picking_contenedor)
                picking_contenedor.carrier_id = nacex_valija.id
                picking_contenedor.with_context(force_send_to_shipper=True).send_to_shipper()
                picking_contenedor.imprimir_operacion()
            else:
                albaran.picking_contenedor = picking_contenedor
                albaran.carrier_id = valija.id
