# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
import datetime, csv, io
from .notifier import Notifier

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'
    #x_sync_status = fields.Integer(default=0)

    FROM_SHOP_DELIVERY_TYPE=[11,16,20,30,36,56,65,86]
    SHOP_RESERVE_LOCATIONS = [122,120,121,123,124,125,937,126]
    SHOP_LOCATIONS = [20, 26, 38, 45, 53, 103, 115, 148] #50: Ferias

    POS_TYPES = [6, 24, 70, 40, 86, 61, 18, 30, 28,90] 
    SHOP_IN_TYPES = [29, 64, 85, 55, 35, 23, 13, 8]
    FROM_SHOP_RETURN_TYPE = [48, 49, 50, 51, 52, 60, 72, 92]  
    OTHER_TYPES = [62, 2, 53, 100, 3] #SCRAPPED_IN_TYPE_ID, PURCHASE_TRANSFER_TYPE, FROM_TRANSLOAN_TO_SEGOVIA, FROM_SHOPS_TO_SEGOVIA_TYPE, PICK_TYPE
    DISTRI_TYPES = [104, 102, 103] #Distri pick, distri recepciones, distri out
    INTERNAL_TYPES = [33,59,10,15,21,39,68,89] #Reservas
    SEGOVIA_INTERNAL_TYPES = [4]
    # 3: Al cambiar el filtro se dejaron sin procesar las salidas de Segovia. Más abajo comprueba que no sean ventas web por el 'canal de ventas' (team_id).
 
    # NO se tienen que hacer:
    INTERNAL_TYPES = [4] # Por ejemplo para reponer la balda de Amazon
    OTHER_NOT_TYPES = [73, 78, 74] # Kame

    ALLOWED_OPERATION_TYPES = FROM_SHOP_DELIVERY_TYPE + POS_TYPES + SHOP_IN_TYPES + FROM_SHOP_RETURN_TYPE + OTHER_TYPES + DISTRI_TYPES + INTERNAL_TYPES + SEGOVIA_INTERNAL_TYPES
    # Faltan las de reservas
    NOT_ALLOWED_OPERATION_TYPES = INTERNAL_TYPES + OTHER_NOT_TYPES

    def setPartnerCarrier(self):
        # TODO: Migración => Revisar con datos como funcionaria la acción automatizada
        for picking in self:
            if not picking.picking_type_id.id == 5 or not picking.partner_id or not picking.partner_id.property_delivery_carrier_id:
                return False
            if not picking.partner_id or not picking.partner_id.property_delivery_carrier_id:
                return False

            newCarrierId = picking.partner_id.property_delivery_carrier_id.id
            # If valija
            if newCarrierId == 9:
                if picking.origin.endswith("-DHL"):
                    newCarrierId = 14 # DHL Carry

            picking.write({'carrier_id' : newCarrierId})

    def send_to_shipper(self):
        # TODO: Migración => Metodo nuevo posterior a refactorizacion para V16
        if self.carrier_id.id == 13 and self.number_of_packages > 1:
            _logger.info(f"Zacalog: send_to_shipper")
            self.write({
                'carrier_id': 15,
            })

        return super(Picking, self).send_to_shipper()

    def get_label_dhl_txt(self):
        if self.carrier_id.delivery_type == 'dhl_parcel':
            attach = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'stock.picking'),
                ('res_id', '=', self.id),
                ('index_content', '!=', False),
                ('mimetype', '=', 'text/plain'),
                ('type', '=', 'binary')
            ], order="create_date desc", limit=1)
            if attach:
                return attach.index_content
        return None
        
    def sync(self):             
        if not self.env['res.config.settings'].getSyncerActive():
            _logger.warning("Zacalog: Syncer not active.")
            return
        someTimeAgo = datetime.datetime.now() - datetime.timedelta(days = 1)
        args = [
            ('state', 'in', ['done', 'assigned', 'waiting', 'cancel', 'confirmed']),
            ('write_date', '>=', someTimeAgo), #.strftime('%Y-%m-%d %H:%M:%S')), #'2022-01-30 17:42:24
            ('location_id', 'not in', [14, 1720]), # Segovia output
            ('x_status', 'in', [0, '0', False]), #, 601, 602, 607]), #607: snooze
            #('picking_type_id', 'in', allowedOperationTypes),
        ]
        pickings = self.search(args)
        for picking in pickings:                
            if picking.picking_type_id.id in self.NOT_ALLOWED_OPERATION_TYPES:
                msg = f"{picking.picking_type_id.name} ({picking.picking_type_id.id}) es uno de los tipos NO permitidos"
                _logger.warning(f"Zacalog: Syncer {msg}")
                self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, msg, "syncer", Notifier.LEVEL_WARNING)
                continue
            
            #TODO: La balda de Amazon no debería contar para el stock. No es crítico porque son solo nuestros juegos.
            
            if not picking.picking_type_id.id in self.ALLOWED_OPERATION_TYPES:
                msg = f"{picking.name} {picking.picking_type_id.name} ({picking.picking_type_id.id}) no es uno de los tipos permitidos"
                _logger.warning(f"Zacalog: Syncer {msg}")
                self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, msg, "syncer", Notifier.LEVEL_WARNING)
            
            #ready = True
            if picking.state == 'confirmed' and picking.group_id:
                # En espera y con grupo de abastecimento
                groups = self.env['procurement.group'].search([('id', '=', picking.group_id.id)])
                for group in groups:
                    if not group.sale_id:
                        continue # Si viene de un abastecimiento sin venta, no procesamos los 'en espera'
                    #_logger.info(f"Zacalog: El picking {self.name} ({self.state}) ha sido modificado. Grupo: {self.group_id.id}; sale: {group.sale_id.id} ({ready})")

            #if not ready:
            #    return
            
            team = False
            if picking.picking_type_id.id == 3: #self.SEGOVIA_PICK_TYPE_ID
                if picking.sale_id:
                    team = picking.sale_id.team_id.id #6: web, 11: pickOp, 14: amazon

            #Esto ya no debería ocurrir TODO: Poner una alerta si pasa
            #if self.partner_id:
            #    if "zacatrus" in self.partner_id.name.lower():
            #        parents = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
            #        for parent in parents:
            #            if parent.parent_id and parent.parent_id.id == 1: # Is Zacatrus
            #                interShopMove = True
            
            if team == 6: #Already decreased in Magento
                if picking.state == 'cancel': # If it is a cancel, we have to return stock to Odoo manually
                    self._syncMagento(picking, True) # reverse = True (último parámetro)
                else:
                    self.write({"x_status": 1})
                    continue
            elif picking.picking_type_id.id in self.SEGOVIA_INTERNAL_TYPES:
                if picking.picking_type_id.id == 936 or picking.location_dest_id.id == 936: #AMAZON_LOCATION_ID
                    if picking.state == 'done':
                        self._syncMagento(picking)
                else:
                    picking.write({"x_status": 1}) # Movimientos internos no se procesan en Segovia
            elif team in [14]: #Amazon: Lo de Amazon no se procesa porque la balda de amazon está fuera del stock
                picking.write({"x_status": 1})
            elif picking.state == 'cancel':
                picking.write({"x_status": 1}) #Todos los cancelados
            elif (picking.picking_type_id.id in Picking.FROM_SHOP_DELIVERY_TYPE #Envíos que salen de tiendas
                and picking.location_dest_id.id != 10 #picking.INTER_COMPANY_LOCATION_ID
                #and not interShopMove
                ):
                #self._syncMagento() # OJO: Tengo dudas, Creo que no debe hacerse porque viene de magento y ya debería estar al día. Nunca ha estado.
                if self.sale_id:
                    if picking.sale_id['x_shipping_method'] not in ['zacaship', 'stock_pickupatstore']:
                        msg = f"Esto es un pedido que sale de tienda, pero no es ni una recogida ni un Trus ({picking.sale_id['x_shipping_method']})"
                        self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, msg, "syncer", Notifier.LEVEL_WARNING)
                                            
                    #if self.sale_id['x_shipping_method'] == 'zacaship':
                    #    self._syncGlovo(self, self.sale_id)                                
                    #if self.sale_id['x_shipping_method'] == 'stock_pickupatstore':
                    #    self._syncPickupatstore(self, self.sale_id)
            else:
                if self.picking_type_id.id in [28]: #ferias #TODO: ¿por qué?
                    self.write({"x_status": 1})
                else:
                    self._syncMagento(picking) #sincroniza cualquier otra cosa
                    
        if self.env['res.config.settings'].getSyncerSyncActive():
            self.env['zacatrus.connector'].procStockUpdateQueue()

    sourceCodes = {
        13: "WH",
        20: "M",
        103: "P",
        53: "B",
        38: "V",
        26: "S",
        45: "I",
        115: "Z",
        148: "A",
        #59: "FR_TL"
        1717: "FR_TL"
    }

    def _syncMagento(self, picking, reverse = False):
        sourceCode = None

        #self.env['zacatrus.connector']
        dests = self.env['stock.location'].search([('id', '=', picking.location_dest_id.id)])
        for dest in dests:
            parentLocationDestId = dest.location_id.id
        froms = self.env['stock.location'].search([('id', '=', picking.location_id.id)])
        for _from in froms:
            parentLocationId = _from.location_id.id

        # Warehouse moves
        shopLocations = Picking.SHOP_RESERVE_LOCATIONS + Picking.SHOP_LOCATIONS + [13, 1717]
        if picking.location_dest_id.id in shopLocations or parentLocationDestId in [13, 11, 1717, 1716]:
            out = False
            if not picking.location_dest_id.id in self.sourceCodes:
                sourceCode = "WH"
            else:
                sourceCode = self.sourceCodes[picking.location_dest_id.id]
        elif picking.location_id.id in shopLocations or parentLocationId in [13, 1717]:
            out = True
            if not picking.location_id.id in self.sourceCodes:
                sourceCode = "WH"
            else:
                sourceCode = self.sourceCodes[picking.location_id.id]
        else:
            self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, f"{picking.name} is not a warehouse move", "syncer", Notifier.LEVEL_WARNING)
            return

        if sourceCode:
            if reverse:
                self._syncMoves(picking, not out, sourceCode)
            else:
                self._syncMoves(picking, out, sourceCode)
        
    def _syncMoves(self, picking, out, sourceCode):
        qtyField = 'quantity_done' if picking.state == 'done' else 'product_uom_qty'
        
        os = self.env['stock.move'].search([("picking_id", "=", picking.id)])
        for o in os:
            product = o.product_id
            if o[qtyField]:
                if out:
                    self.env['zacatrus.connector'].decreaseStock(product.default_code, o[qtyField], False, sourceCode)
                else:
                    self.env['zacatrus.connector'].increaseStock(product.default_code, o[qtyField], picking.picking_type_id.id == 2, sourceCode)
        
        picking.write({"x_status": 1})
        #self.getMagentoConnector().procStockUpdateQueue()

    def _syncPickupatstore(self, sale):
        if sale['team_id'][0] == 6:
            sc = self.env['zacatrus_base.slack']
            channel = sc.getSlackChannelByLocation(self.location_id.id)

            if self.state in ['assigned', 'confirmed']: 
                if self.x_status == 0:
                    sc.sendWarn(f"Ha llegado un nuevo pedido para recogida en tienda: {self.name} (#{sale.client_order_ref}). Por favor, prepáralo (en Odoo) y guárdalo en una bolsa hasta que vengan a buscarlo. Cuando termines aviso al cliente.", channel)
                    self.write({"x_status": 601})
            elif self.state == 'done' and self.x_status in [601, 602, 607]:
                self.write({"x_status": 603})
                try:
                    msg = f"No he conseguido avisar al cliente. Por favor, llama o manda un email para que pase a recoger su pedido ({sale.client_order_ref})."
                    if self.notifyCustomer(self.sale_id):
                        msg = f"Ok, cliente avisado  (pedido #{sale.client_order_ref})."
                except Exception as e:
                    msg = f"No he conseguido avisar al cliente. Por favor, llama o manda un email para que pase a recoger su pedido ({sale.client_order_ref}). ({e})"

                sc.sendWarn(msg, channel)

    def notifyCustomer(self, order):
        if order.x_shipping_method.endswith('pickupatstore'):
            args = [("id", "=", order["partner_shipping_id"][0])]
            partners = self.env['res.partner'].search_read( args )
            for partner in partners:
                try:
                    self.sendMail(partner["email_formatted"], partner["zip"], order["client_order_ref"], partner["name"])
                    
                    order.write({"x_status": 12})
                    #self._writeOrderNote(order.id, "[Tito] Cliente avisado para que pase a recoger.")
                    msg = "[Tito] Cliente avisado para que pase a recoger."
                    m = {
                        'model': 'sale.order',
                        'res_id': order.id,
                        'body': f"<p>{msg}</p>",
                        'description': f"{msg}",
                        'message_type': 'comment',
                        'subtype_id': 2,
                        'mail_activity_type_id': False,
                        'is_internal': True,             
                    }
                    self.env['mail.message'].create(m)
                    return True
                except:
                    _logger.error(f"Zacalog: {msg}")
                    msg = f"Could not notify customer for order {order.name}."
                    self.env['zacatrus_base.notifier'].notify('sale.order', order.id, msg, "syncer", Notifier.LEVEL_ERROR)
                        
        return False

    def sendMail(self, to, zip, orderId, name):
        shop = self.env['zacatrus.zconta'].getShopByZip(zip)
        data = {
            'order_id': orderId,'name': name, 'email': to, "url": shop['url'], 'address': shop['address']
        }
        mail = self.env['zacatrus_base.pickupmail'].create(data)
        mail.send()

    def _syncGlovo(self, picking, sale):
        if not sale.team_id.id == 6:
            return
        
        sc = self.env['zacatrus_base.slack']
        channel = sc.getSlackChannelByLocation(picking.location_id.id)

        if picking.state in ['assigned', 'confirmed', 'done'] and picking.x_status == 0:
            if picking.state in ['assigned', 'confirmed']:
                pdfName = f"report_{picking['name']}.pdf".replace("/", "_")
                content = self.env['zacatrus.zconta'].getPickingSlip( picking.id, "zacatrus_base.report_deliveryslip_ticket" )

                sc.sendWarn(f"Ha llegado un nuevo pedido para Glovo: {pdfName}", channel)

                sc.sendFile( content, channel, pdfName )
            picking.write({"x_status": 601})
        elif picking.state == 'done' and picking.x_status in [601, 602]:
            partners = self.env['res.partner'].search([('id', '=', picking.partner_id.id)])
            for partner in partners:
                address = f"{partner.street} {partner.street2 if partner.street2 else ''}, {partner.zip} {partner.city}"
                details = f"{partner.street} {partner.street2 if partner.street2 else ''}"

                #TODO:
                carrierOrderId = self._getGlovoConnector().create(
                    picking.location_id.id, address, details, partner.name, partner.phone
                )
                if carrierOrderId:
                    data = {
                        "x_status": 603, 
                        "carrier_id": 11,
                        "carrier_tracking_ref": carrierOrderId
                    }
                    picking.write(data)
                    sc.sendWarn(f"Ok, aviso al rider para que lo recoja: {picking.name}", channel)
                else:
                    msg = f"NO puedo avisar al rider para que recoja {picking.name}"
                    sc.sendWarnLimited(msg, channel, f"{picking.id}")
