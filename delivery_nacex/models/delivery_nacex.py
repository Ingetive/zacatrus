# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf

from .nacex_request import NacexRequest, SERVICIOS_PENINSULA, SERVICIOS_INTERNACIONALES

_logger = logging.getLogger(__name__)


class ProviderNacex(models.Model):
    _inherit = 'delivery.carrier'
    
    delivery_type = fields.Selection(selection_add=[
        ('nacex', "Nacex")
    ], ondelete={'nacex': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    nacex_user = fields.Char("Usuario", groups="base.group_system")
    nacex_password = fields.Char("Contraseña", groups="base.group_system")
    nacex_tipo_servicio_peninsula = fields.Selection(SERVICIOS_PENINSULA, string="Tipo de servicio península")
    nacex_tipo_servicio_internacional = fields.Selection(SERVICIOS_INTERNACIONALES, string="Tipo de servicio península")
    nacex_delegacion_cliente = fields.Char("Delegación cliente")
    nacex_code_cliente = fields.Char("Código cliente")
    
    def nacex_rate_shipment(self, order):
        nacex = NacexRequest(self.log_xml)
        check_value = nacex.check_required_value(self, order.partner_shipping_id, order.warehouse_id.partner_id, order=order)
        if check_value:
            return {
                'success': False, 
                'price': 0.0,
                'error_message': check_value,
                'warning_message': False
            }
        
        try:
            price = nacex.rate(order, self)
        except UserError as e:
            return {
                'success': False,
                'price': 0.0,
                'error_message': e.args[0],
                'warning_message': False
            }
        
        if order.currency_id.name != 'EUR':
            quote_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
            price = quote_currency._convert(price, order.currency_id, order.company_id, order.date_order or fields.Date.today())
            
        return {
            'success': True,
            'price': price,
            'error_message': False,
            'warning_message': False
        }
    
    def nacex_send_shipping(self, pickings):
        _logger.warning("nacex_send_shipping")
        res = []
        nacex = NacexRequest(self.log_xml)
        
        for picking in pickings:
            check_value = nacex.check_required_value(self, picking.partner_id, picking.picking_type_id.warehouse_id.partner_id, picking=picking)
            
            if check_value:
                raise UserError(check_value)
                
            shipping = nacex.send_shipping(picking, self)
            
            raise UserError("FIn")
            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.company
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            if order_currency.name == "EUR":
                carrier_price = shipping['price']
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
                carrier_price = quote_currency._convert(shipping['price'], order_currency, company, order.date_order or fields.Date.today())
                
            
            carrier_tracking_ref = shipping['num_recogida']
            logmessage = (_("""
                El envío de Nacex ha sido creado <br/> 
                <b>Número de seguimiento: </b> %s <br/>
                <b>Fecha prevista de recogida:</b> %s""") % (carrier_tracking_ref, shipping['fecha_recogida']))
            picking.message_post(body=logmessage)

            shipping_data = {
                'exact_price': carrier_price,
                'tracking_number': carrier_tracking_ref
            }
            res = res + [shipping_data]
        return res
    
    def _nacex_convert_weight(self, weight):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_kgm'), round=False)

    