# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_company = fields.Char("Empresa")
    x_droppoint = fields.Integer('Punto Nacexshop')
    x_status = fields.Integer('Estado de importación (magento)')
    x_tarjezaca = fields.Float('Cantidad pagada con Tarjezaca')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        for record in res:
            record.change_delivery()
        return res

    def change_delivery(self):
        carrier_nacex_peninsula = self.env.ref("delivery_nacex.delivery_carrier_nacex_peninsula")
        carrier_nacex_canarias = self.env.ref("delivery_nacex.delivery_carrier_nacex_canarias")
        carrier_nacex_baleares = self.env.ref("delivery_nacex.delivery_carrier_nacex_baleares")
        carrier_dhl_b2c_francia = 13

        for r in self:
            carrier_id = False
            if not self.env.context.get("without_shipping_method"):
                if r.x_shipping_method == 'pickupatstore':
                    carrier_id = self.env.ref("delivery_nacex.delivery_carrier_valija").id
                elif r.x_shipping_method == 'mageworxpickup':
                    carrier_id = self.env.ref("delivery_nacex.delivery_carrier_nacex_shop").id
                

            #if r.x_shipping_method in ['freeshippingadmin', 'tablerate'] or r.team_id.id in [14] or self.env.context.get("without_shipping_method"): # team_id 14 es Amazon
            #if r.x_shipping_method in ['freeshippingadmin', 'tablerate'] or self.env.context.get("without_shipping_method"):
            # Team id 16 = Amazon fr
            if r.x_shipping_method in ['freeshippingadmin', 'tablerate'] or self.env.context.get("without_shipping_method") or r.team_id.id in [16]:
                carriers = self.env['delivery.carrier'].search(['|', ('company_id', '=', False), ('company_id', '=', r.company_id.id)])
                available_carrier_ids = carriers.available_carriers(r.partner_shipping_id) if r.partner_id else carriers
                if carrier_nacex_canarias.id in available_carrier_ids.ids:
                    carrier_id = carrier_nacex_canarias.id
                elif carrier_nacex_baleares.id in available_carrier_ids.ids:
                    carrier_id = carrier_nacex_baleares.id
                elif carrier_nacex_peninsula.id in available_carrier_ids.ids:
                    carrier_id = carrier_nacex_peninsula.id
                elif carrier_dhl_b2c_francia in available_carrier_ids.ids:
                    carrier_id = carrier_dhl_b2c_francia
                elif False: # TODO: Asignar carriers externos para Transloan (Distri, Francia, ...) y activar
                    for carrierId in available_carrier_ids:
                        # TODO: Discriminar por partner_shipping_id (ECI, Fnac, ...), picking_type_id y pais
                        carrier_id = carrierId
                        _logger.info(f"Zacalog: Asignado carrier {carrier_id}.")
                        break
                
            if carrier_id:
                r.write({'carrier_id': carrier_id})
            #else:
            #    _logger.warning(f"Zacalog: Al Pedido de Venta {r.name} no se le ha podido asignar ningún método de envío.")
                