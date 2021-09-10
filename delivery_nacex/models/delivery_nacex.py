# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import api, models, fields, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import pdf

from .nacex_request import NacexRequest

_logger = logging.getLogger(__name__)

TIPOS_SERVICIO = [
    ('peninsula', "España, Portugal y Andorra"),
    ('internacional', "Internacional")
]

# Servicios España, Portugal y Andorra
SERVICIOS_PENINSULA = [
    ('01', 'NACEX 10:00H'),
    ('02', 'NACEX 12:00H'),
    ('03', 'INTERDIA'),
    ('04', 'PLUS BAG 1'),
    ('05', 'PLUS BAG 2'),
    ('06', 'VALIJA'),
    ('07', 'VALIJA IDA Y VUELTA'),
    ('08', 'NACEX 19:00H'),
    ('09', 'PUENTE URBANO'),
    ('10', 'DEVOLUCION ALBARAN CLIENTE'),
    ('11', 'NACEX 08:30H'),
    ('12', 'DEVOLUCION TALON'),
    ('14', 'DEVOLUCION PLUS BAG 1'),
    ('15', 'DEVOLUCION PLUS BAG 2'),
    ('17', 'DEVOLUCION E-NACEX'),
    ('21', 'NACEX SABADO'),
    ('22', 'CANARIAS MARITIMO'),
    ('24', 'CANARIAS 24H'),
    ('25', 'NACEX PROMO'),
    ('26', 'PLUS PACK'),
    ('27', 'E-NACEX'),
    ('28', 'PREMIUM'),
    ('29', 'NX-SHOP VERDE'),
    ('30', 'NX-SHOP NARANJA'),
    ('31', 'E-NACEX SHOP'),
    ('33', 'C@MBIO'),
    ('48', 'CANARIAS 48H'),
    ('88', 'INMEDIATO'),
    ('90', 'NACEX.SHOP'),
    ('91', 'SWAP'),
    ('95', 'RETORNO SWAP'),
    ('96', 'DEV. ORIGEN'),
]

# Servicios internacionales
SERVICIOS_INTERNACIONALES = [
    ('E', 'EURONACEX TERRESTRE'),
    ('F', 'SERVICIO AEREO'),
    ('G', 'EURONACEX ECONOMY'),
    ('H', 'PLUSPACK EUROPA'),
]

# Quién se hace cargo del importe del servicio de transporte.
TIPOS_DE_COBRO = [
    ('O', 'Origen'), # Factura la agencia origen del envío
    ('D', 'Destino'), # Factura la agencia de entrega del envío
    ('T', 'Tercera'), # Factura una tercera agencia
]

# Envases España, Portugal y Andorra
ENVASES_PENINSULA = [
    ('0', 'Docs'), # Documentos, papel
    ('1', 'Bag'), # Bolsa de envío Nacex normalizada.
    ('2', 'Pag'), # Caja de cartón, varias medidas
]

# Envases Internacionales
ENVASES_INTERNACIONALES = [
    ('D', 'Documentos'), # Documentos, papel
    ('M', 'Muestras'), # Caja de cartón, varias medidas.
]

VEHICULOS = [
    ('C', "Coche"),
    ('M', "Moto"),
]

ETIQUETAS = [
    ('TECSV4_B', 'TECSV4_B'),
    ('TECEV4_B', 'TECEV4_B'),
    ('TECFV4_B', 'TECFV4_B'),    
    ('ZEBRA_B', 'ZEBRA_B'),
]

class ProviderNacex(models.Model):
    _inherit = 'delivery.carrier'
    
    delivery_type = fields.Selection(selection_add=[
        ('nacex', "Nacex")
    ], ondelete={'nacex': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    nacex_user = fields.Char("Usuario", groups="base.group_system")
    nacex_password = fields.Char("Contraseña", groups="base.group_system")
    nacex_tipo_servicio = fields.Selection(TIPOS_SERVICIO, string="Tipo de servicio", required=True, default="peninsula")
    nacex_tipo_servicio_peninsula = fields.Selection(SERVICIOS_PENINSULA, string="Tipo de servicio España, Portugal y Andorra")
    nacex_tipo_servicio_internacional = fields.Selection(SERVICIOS_INTERNACIONALES, string="Tipo de servicio internacional")
    nacex_tipo_cobro = fields.Selection(TIPOS_DE_COBRO, string="Tipo de cobro")
    nacex_envase_peninsula = fields.Selection(ENVASES_PENINSULA, string="Envases España, Portugal y Andorra")
    nacex_envase_internacional = fields.Selection(ENVASES_INTERNACIONALES, string="Envases internacional")
    nacex_delegacion_cliente = fields.Char("Delegación cliente")
    nacex_code_cliente = fields.Char("Código cliente")
    nacex_vehiculo = fields.Selection(VEHICULOS, string="Vehículo", default="C", required=True)
    nacex_etiqueta = fields.Selection(ETIQUETAS, string="Etiqueta", default="ZEBRA_B", required=True)
    
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
            
            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.company
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            if order_currency.name == "EUR":
                carrier_price = shipping['price']
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
                carrier_price = quote_currency._convert(shipping['price'], order_currency, company, order.date_order or fields.Date.today())
                
            carrier_tracking_ref = shipping['codigo_expedicion']
            imagen_etiqueta = nacex.get_label(carrier_tracking_ref, 'IMAGEN_B', self)
            fichero_etiqueta = nacex.get_label(carrier_tracking_ref, self.nacex_etiqueta, self)

            logmessage = (_("""
                El envío de Nacex ha sido creado <br/> 
                <b>Número de seguimiento: </b> %s <br/>
                <b>Nombre del servicio: </b> %s <br/>
                <b>Hora de la entrega: </b> %s <br/>
                <b>Fecha prevista de recogida:</b> %s""") % (
                    carrier_tracking_ref, 
                    shipping['nombre_servicio'],
                    shipping['hora_entrega'],
                    shipping['fecha_prevista'].strftime("%d/%m/%Y")
            ))
                
            picking.message_post(body=logmessage, attachments=[('imagen_etiqueta.png',imagen_etiqueta)])
            picking.message_post(body='Etiqueta impresora', attachments=[('fichero_etiqueta.txt',fichero_etiqueta)])
                                 
            shipping_data = {
                'exact_price': carrier_price,
                'tracking_number': carrier_tracking_ref
            }
            res = res + [shipping_data]
        return res
    
    def _nacex_convert_weight(self, weight):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_kgm'), round=False)

    