# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_company = fields.Char("Empresa")
    x_droppoint = fields.Integer('Punto Nacexshop')
    x_status = fields.Integer('Estado de importación (magento)')
    
    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        res.change_delivery()
        return res

    def change_delivery(self):
        carrier_nacex_peninsula = self.env.ref("delivery_nacex.delivery_carrier_nacex_peninsula")
        carrier_nacex_canarias = self.env.ref("delivery_nacex.delivery_carrier_nacex_canarias")
        carrier_nacex_baleares = self.env.ref("delivery_nacex.delivery_carrier_nacex_baleares")
        for r in self:
            carrier_id = False
            if not self.env.context.get("without_shipping_method"):
                if r.x_shipping_method == 'pickupatstore':
                    carrier_id = self.env.ref("delivery_nacex.delivery_carrier_valija").id
                elif r.x_shipping_method == 'mageworxpickup':
                    carrier_id = self.env.ref("delivery_nacex.delivery_carrier_nacex_shop").id
                

            #if r.x_shipping_method in ['freeshippingadmin', 'tablerate'] or r.team_id.id in [14] or self.env.context.get("without_shipping_method"): # team_id 14 es Amazon
            #if r.x_shipping_method in ['freeshippingadmin', 'tablerate'] or self.env.context.get("without_shipping_method"):

            if r.x_shipping_method in ['freeshippingadmin', 'tablerate'] or self.env.context.get("without_shipping_method"):
                carriers = self.env['delivery.carrier'].search(['|', ('company_id', '=', False), ('company_id', '=', r.company_id.id)])
                available_carrier_ids = carriers.available_carriers(r.partner_shipping_id) if r.partner_id else carriers
                if carrier_nacex_canarias.id in available_carrier_ids.ids:
                    carrier_id = carrier_nacex_canarias.id
                elif carrier_nacex_baleares.id in available_carrier_ids.ids:
                    carrier_id = carrier_nacex_baleares.id
                elif carrier_nacex_peninsula.id in available_carrier_ids.ids:
                    carrier_id = carrier_nacex_peninsula.id
                
            if carrier_id:
                r.write({'carrier_id': carrier_id})
            else:
                _logger.warning(f"Al Pedido de Venta {r.name} no se le ha podido asignar ningún método de envío.")
                