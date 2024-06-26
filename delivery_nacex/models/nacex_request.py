# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging
import os
import re
import requests
import base64

from urllib.parse import quote
from odoo import _
from datetime import datetime, date
from odoo.exceptions import UserError
from odoo.tools import remove_accents

_logger = logging.getLogger(__name__)


class NacexRequest():
    """ Low-level object intended to interface Odoo recordsets with FedEx,
        through appropriate SOAP requests """

    def __init__(self, debug_logger):
        self.debug_logger = debug_logger
        self.base_url = "http://pda.nacex.com/nacex_ws/ws"
    
    def send_shipping(self, picking, carrier):
        shipping_weight_in_kg = 0.0
        num_bultos = 0
        
        if not picking.bultos>0:
            if picking.package_ids:
                for paquete in picking.package_ids:
                    shipping_weight_in_kg += paquete.weight
                    num_bultos += 1        
            else:
                num_bultos += 1
                for move in picking.move_ids:
                    shipping_weight_in_kg += move.product_qty * move.product_id.weight
            shipping_weight_in_kg = 1.0 #Forzamos a que el peso del envío siempre sea 1.0
        else:
            num_bultos = picking.bultos
            shipping_weight_in_kg = 1.0 #Forzamos a que el peso del envío siempre sea 1.0
        
        bultos = str(num_bultos)
        for i in range(len(str(num_bultos)), 3):
            bultos = "0%s" % bultos
        
        partner_wharehouse = picking.picking_type_id.warehouse_id.partner_id
            
        price = self._get_rate(carrier, partner_wharehouse.zip, picking.partner_id.zip, shipping_weight_in_kg)

        params = {
            "del_cli": carrier.nacex_delegacion_cliente, # Delegación del cliente
            "num_cli": carrier.nacex_code_cliente, # Código del cliente (Nº abonado Nacex)
            "fec": datetime.now().strftime("%d/%m/%Y"), # Fecha de la expedición (dd/mm/yyyy)
            "tip_cob": carrier.nacex_tipo_cobro, # Código de Cobro Nacex
            "bul": bultos, # Número de bultos (Ej. Para 5 bultos, 005)
            "kil": shipping_weight_in_kg, # Peso en Kilos
            "nom_rec": partner_wharehouse.name[:35], # Nombre de recogida
            "dir_rec": partner_wharehouse.street[:60], # Dirección de recogida
            "cp_rec": partner_wharehouse.zip, # Código postal recogida (Ej. 08902)
            "pob_rec": partner_wharehouse.city[:30], # Población de recogida
            "pais_rec": partner_wharehouse.country_id.code, # País de recogida
            "nom_ent": picking.partner_id.name[:50], # Nombre de entrega
            "dir_ent": picking.partner_id.street[:50], # Dirección de entrega
            "pais_ent": picking.partner_id.country_id.code, # País de entrega
            "cp_ent": picking.partner_id.zip, # Código postal entrega (Ej. 08902)
            "pob_ent": picking.partner_id.city[:40], # Población de entrega
            "obs1": picking.note if picking.note else '', # Observaciones, hasta 4 observaciones (obs"n")
            "obs2": picking.name,
            "ref_cli" : picking.sale_id.client_order_ref if picking.sale_id else '',
        }
        
        carrier_nacex_shop = picking.env.ref('delivery_nacex.delivery_carrier_nacex_shop')
        carrier_nacex_valija = picking.env.ref('delivery_nacex.delivery_carrier_nacex_valija')
        if picking.carrier_id.id in [carrier_nacex_shop.id]:
            params.update({
                'tip_pre1': 'S',
                'mod_pre1': 'S',
            })
            if picking.partner_id.phone:
                params.update({'pre1': picking.partner_id.phone})
        
        if picking.carrier_id.id == carrier_nacex_shop.id and picking.sale_id.x_droppoint:
            params.update({'shop_codigo': picking.sale_id.x_droppoint})
        
        if partner_wharehouse.phone:
            params.update({"tel_rec": partner_wharehouse.phone[:15]}) # Teléfono de recogida
        
        if picking.partner_id.phone:
            params.update({"tel_ent": picking.partner_id.phone[:19]}) # Teléfono de entrega
        
        if carrier.nacex_tipo_servicio == 'peninsula':
            params.update({
                "tip_ser": carrier.nacex_tipo_servicio_peninsula, # Código de Servicio Nacex
                "tip_env": carrier.nacex_envase_peninsula, # Código de envase Nacex
            })
        elif carrier.nacex_tipo_servicio == 'internacional':
            params.update({
                "tip_ser": carrier.nacex_tipo_servicio_internacional, # Código de Servicio Nacex
                "tip_env": carrier.nacex_envase_internacional, # Código de envase Nacex
            })
            
        if picking.carrier_id.id == carrier_nacex_valija.id:
            params.update({
                "nom_ent": "Zacatrus",
                "tel_ent": "910767606"
            })
        
        code, result = self._send_request('putExpedicion', carrier, params)
        
        try:
            fecha_prevista = datetime.strptime(result[10], '%d/%m/%Y')
        except:
            fecha_prevista = None
        
        return {
            'price': price,
            'codigo_expedicion': result[0],
            'carrier_tracking_ref': result[1],
            'num_seguimiento': result[1],
            'color_caja': result[2],
            'ruta': result[3],
            'codigo_agencia_con_formato': result[4],
            'nombre_agencia_entrega': result[5],
            'telefono_entrega': result[6],
            'nombre_servicio': result[7],
            'hora_entrega': result[8],
            'codigo_barras': result[9],
            'fecha_prevista': fecha_prevista,
        }
        
    def rate(self, order, carrier):
        weight_in_kg = carrier._nacex_convert_weight(order._get_estimated_weight())
        return self._get_rate(carrier, order.warehouse_id.partner_id.zip, order.partner_shipping_id.zip, weight_in_kg)
    
    def _get_rate(self, carrier, cp_rec, cp_ent, weight_in_kg):
        params = {
            "cp_rec": cp_rec,
            "cp_ent": cp_ent,
            "kil": weight_in_kg,
#             "alto": 5,
#             "ancho": 5,
#             "largo": 5
        }
        
        if carrier.nacex_code_cliente and carrier.nacex_delegacion_cliente:
            params.update({
                'del_cli': carrier.nacex_delegacion_cliente,
                'num_cli': carrier.nacex_code_cliente
            })
        
        if carrier.nacex_tipo_servicio == 'peninsula':
            params.update({
                "tip_ser": carrier.nacex_tipo_servicio_peninsula,
                "tip_env": carrier.nacex_envase_peninsula,
            })
        elif carrier.nacex_tipo_servicio == 'internacional':
            params.update({
                "tip_ser": carrier.nacex_tipo_servicio_internacional,
                "tip_env": carrier.nacex_envase_internacional,
            })
    
        code, result = self._send_request('getValoracion', carrier, params)
        try:
            return float(result[1].replace(",", "."))
        except:
            raise UserError(_("Error al convertir el precio."))
    
    def get_label(self, codigo_expedicion, etiqueta, carrier):
        params = {
            "codExp": codigo_expedicion,
            "modelo": etiqueta,
        }
        #Debido a la gran cantidad de veces que se produce "Incorrect padding" generamos tantas llamadas como sea necesario con un maximo de 10
        max_intentos = 10
        fichero = None
        while fichero is None and max_intentos>0:
            code, result = self._send_request('getEtiqueta', carrier, params)
            if not result:
                _logger.warning("Error al intentar obtener la etiqueta.")
                max_intentos -= 1
                continue

            label = result[0]
            if etiqueta == 'IMAGEN_B':
                pad = len(label)%4
                label += "="*pad
                fichero = base64.urlsafe_b64decode(label)
            else :
                try:
                    fichero = result[0].encode('iso-8859-1').decode()
                except:
                    fichero = result[0]

        return fichero
                
    def nacex_cancel_shipment(self, picking):
        params = {
            "expe_codigo": picking.codigo_expedicion
        }

        code, result = self._send_request('cancelExpedicion', carrier, params)

        if result["Expedición cancelada con éxito"]:
            picking.message_post(body=_(u'Shipment #%s has been cancelled', picking.codigo_expedicion))
            picking.write({
                'etiqueta_envio_zpl' : '',
                'carrier_tracking_ref': '',
                'codigo_expedicion': '',
                'carrier_price': 0.0
            })
        else:
            raise UserError(result['errors_message'])
            
    def check_required_value(self, carrier, recipient, shipper, order=False, picking=False):
        carrier = carrier.sudo()
        if not carrier.nacex_user:
            return _("El usuario es obligatorio, modificalo en la configuración del método de envío.")
        
        if not carrier.nacex_password:
            return _("La contraseña es obligatoria, modificalo en la configuración del método de envío.")
        
        if carrier.nacex_tipo_servicio:
            if carrier.nacex_tipo_servicio == 'peninsula':
                envase = carrier.nacex_envase_peninsula
                tipo_servicio = carrier.nacex_tipo_servicio_peninsula
            elif carrier.nacex_tipo_servicio == 'internacional':
                envase = carrier.nacex_envase_internacional
                tipo_servicio = carrier.nacex_tipo_servicio_internacional
                
            if not envase:
                return _("El de envase es obligatorio, modificalo en la configuración del método de envío.")

            if not tipo_servicio:
                return _("El tipo de servicio es obligatorio, modificalo en la configuración del método de envío.")
        else:
            return _("El tipo de servicio es obligatorio, modificalo en la configuración del método de envío.")

        recipient_required_field = ['city', 'zip', 'country_id']
        if not recipient.street and not recipient.street2:
            recipient_required_field.append('street')
        res = [field for field in recipient_required_field if not recipient[field]]
        if res:
            return _("La dirección del cliente es obligatoria (Campos obligatorio(s) :\n %s)") % ", ".join(res).replace("_id", "")

        if not recipient.phone:
            return _("El teléfono del cliente es obligatorio.")
        
        shipper_required_field = ['city', 'zip', 'country_id']
        if not shipper.street and not shipper.street2:
            shipper_required_field.append('street')
        res = [field for field in shipper_required_field if not shipper[field]]
        if res:
            return _("The address of your company warehouse is missing or wrong (Missing field(s) :\n %s)") % ", ".join(res).replace("_id", "")

#         if not shipper.phone:
#             return _("El teléfono del almacén de la compañia es obligatorio.")
        
        if order:
            if not order.order_line:
                return _("Por favor añada al menos una línea de compra.")
            
            for line in order.order_line.filtered(lambda line: not line.product_id.weight and not line.is_delivery and line.product_id.type not in ['service', 'digital'] and not line.display_type):
                return _('El precio estimado no se puede calcular porque falta el peso de los productos.')
        return False
    
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
        
        try:
            response = requests.request("GET", self.base_url, headers={}, params=params, timeout=15)
        except requests.exceptions.Timeout:
            raise UserError(_('El servicio de Nacex no response, por favor, intentelo más tarde.'))
            
        result = response.text.split("|")
        if result[0] == "ERROR":
            raise UserError(_("El servicio de Nacex ha dado error. \nMensaje del error: %s\nCódigo del error: %s" % (result[1], result[2])))
        
        return response.status_code, result
