# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging
import os
import re
import requests

from odoo import _
from datetime import datetime, date
from odoo.exceptions import UserError
from odoo.tools import remove_accents

_logger = logging.getLogger(__name__)

# Quién se hace cargo del importe del servicio de transporte.
TIPOS_DE_COBRO = [
    ('O', 'Origen'), # Factura la agencia origen del envío
    ('D', 'Destino'), # Factura la agencia de entrega del envío
    ('T', 'Tercera'), # Factura una tercera agencia
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


class NacexRequest():
    """ Low-level object intended to interface Odoo recordsets with FedEx,
        through appropriate SOAP requests """

    def __init__(self, debug_logger):
        self.debug_logger = debug_logger
        self.base_url = "http://pda.nacex.com/nacex_ws/ws"
            
    def check_required_value(self, carrier, recipient, shipper, order=False, picking=False):
        carrier = carrier.sudo()
        if not carrier.nacex_user:
            return _("El usuario es obligatorio, modificalo en la configuración del método de envío.")
        
        if not carrier.nacex_password:
            return _("La contraseña es obligatoria, modificalo en la configuración del método de envío.")

        recipient_required_field = ['city', 'zip', 'country_id']
        if not recipient.street and not recipient.street2:
            recipient_required_field.append('street')
        res = [field for field in recipient_required_field if not recipient[field]]
        if res:
            return _("La dirección del cliente es obligatoria (Campos obligatorio(s) :\n %s)") % ", ".join(res).replace("_id", "")

        shipper_required_field = ['city', 'zip', 'country_id']
        if not shipper.street and not shipper.street2:
            shipper_required_field.append('street')

        res = [field for field in shipper_required_field if not shipper[field]]
        if res:
            return _("The address of your company warehouse is missing or wrong (Missing field(s) :\n %s)") % ", ".join(res).replace("_id", "")

        if order:
            if not order.order_line:
                return _("Por favor añada al menos una línea de compra.")
            
            for line in order.order_line.filtered(lambda line: not line.product_id.weight and not line.is_delivery and line.product_id.type not in ['service', 'digital'] and not line.display_type):
                return _('El precio estimado no se puede calcular porque falta el peso de los productos.')
        return False
    
    def send_shipping(self, picking, carrier):
        shipping_weight_in_kg = 0.0
        for move in picking.move_lines:
            shipping_weight_in_kg += move.product_qty * move.product_id.weight
            
        partner_wharehouse = picking.picking_type_id.warehouse_id.partner_id
            
        price = self._get_rate(carrier, partner_wharehouse.zip, picking.partner_id.zip, shipping_weight_in_kg)
        
        params = {
            "delcli": carrier.nacex_delegacion_cliente, # Delegación del cliente
            "numcli": carrier.nacex_code_cliente, # Código del cliente (Nº abonado Nacex)
            "fecha": datetime.now().strftime("%d/%m/%Y"), # Fecha de la expedición con formato dd/MM/aaaa
            "cobro": TIPOS_DE_COBRO[0], # Código de Cobro Nacex
            "servicio": SERVICIOS_PENINSULA[0], # Código de Servicio Nacex
            "envase": ENVASES_PENINSULA[2], # Código de envase Nacex
            "bultos": "001", # Número de bultos (Ej. Para 5 bultos, 005)
            "peso": shipping_weight_in_kg, # Peso en Kilos
            "nomrec": partner_wharehouse.name, # Nombre de recogida
            "dirrec": partner_wharehouse.street, # Dirección de recogida
            "cprec": partner_wharehouse.zip, # Código postal recogida (Ej. 08902)
            "pobrec": partner_wharehouse.city, # Población de recogida
            "telrec": partner_wharehouse.phone, # Teléfono de recogida
            "nom_ent": picking.partner_id.name, # Nombre de entrega
            "dir_ent": picking.partner_id.street, # Dirección de entrega
            "pais_ent": picking.partner_id.country_id.code, # País de entrega
            "cp_ent": picking.partner_id.zip, # Código postal entrega (Ej. 08902)
            "pob_ent": picking.partner_id.city, # Población de entrega
            "tel_ent": picking.partner_id.phone, # Teléfono de entrega
            "hora_ini1": "09:00", # Horario de recogida inicial de mañanas con formato hh:mm
            "hora_fin1": "14:00", # Horario de recogida final de mañanas con formato hh:mm
            "vehiculo": "C", # Vehículo recogida (C = coche / M: Moto)
            "solicitante": picking.partner_id.name, # Solicitante de la recogida
            "email_solicitante": picking.partner_id.email, # Email del solicitante de la recogida
        }
        
        code, result = self._send_request('putRecogida', carrier, params)
        
        _logger.warning(price)
        
        return {
            'price': price,
            'num_recogida': result[1],
            'fecha_recogida': result[2]
        }
        
    def rate(self, order, carrier):
        weight_in_kg = carrier._nacex_convert_weight(order._get_estimated_weight())
        return self._get_rate(carrier, order.warehouse_id.partner_id.zip, order.partner_shipping_id.zip, weight_in_kg)
    
    def _get_rate(self, carrier, cp_rec, cp_ent, weight_in_kg):
        params = {
            "cp_rec": cp_rec,
            "cp_ent": cp_ent,
            "tip_ser": SERVICIOS_PENINSULA[0],
            "tip_env": ENVASES_PENINSULA[2],
            "kil": weight_in_kg,
#             "alto": 5,
#             "ancho": 5,
#             "largo": 5
        }
    
        code, result = self._send_request('getValoracion', carrier, params)
        try:
            return float(result[1].replace(",", "."))
        except:
            raise UserError(_("Error al convertir el precio."))

    def parse_data(self, data):
        data_string = ""
        for key, value in data.items():
            if data_string:
                data_string += "|"
            data_string += "%s=%s" % (key, value)
            
        return data_string

    def _send_request(self, action, carrier, data={}):
        params = {
            "user": carrier.nacex_user,
            "pass": carrier.nacex_password,
            "method": action,
            "data": self.parse_data(data)
        }
        
        self.debug_logger("\n%s\n%s" % (self.base_url, params), action)
        
        _logger.warning(self.base_url)
        _logger.warning(params)
        
        try:
            response = requests.request("GET", self.base_url, headers={}, params=params, timeout=15)
        except requests.exceptions.Timeout:
            raise UserError(_('El servicio de Nacex no response, por favor, intentelo más tarde.'))
            
        result = response.text.split("|")
        if result[0] == "ERROR":
            raise UserError(_("El servicio de Nacex ha dado error. \nMensaje del error: %s\nCódigo del error: %s" % (result[1], result[2])))
        
        _logger.warning(response)
#         self.debug_logger("%s\n%s" % (response.status_code, response.text), 'bpost_response_%s' % action)

        return response.status_code, result