import logging
from odoo import models
import datetime
from .notifier import Notifier

_logger = logging.getLogger(__name__)

class Syncer(models.TransientModel):
    _name = 'zacatrus.syncer'
    _description = 'Zacatrus Syncer'
        
    FROM_SHOP_DELIVERY_TYPE = [11,16,20,30,36,56,65,86]
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
    #INTERNAL_TYPES = [4] # Por ejemplo para reponer la balda de Amazon
    OTHER_NOT_TYPES = [73, 78, 74] # Kame

    ALLOWED_OPERATION_TYPES = FROM_SHOP_DELIVERY_TYPE + POS_TYPES + SHOP_IN_TYPES + FROM_SHOP_RETURN_TYPE + OTHER_TYPES + DISTRI_TYPES + INTERNAL_TYPES + SEGOVIA_INTERNAL_TYPES
    # Faltan las de reservas
    NOT_ALLOWED_OPERATION_TYPES = OTHER_NOT_TYPES

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
        pickings = self.env['stock.picking'].search(args)
        for picking in pickings:                
            if picking.picking_type_id.id in self.NOT_ALLOWED_OPERATION_TYPES: #Basicamente Kame
                msg = f"{picking.picking_type_id.name} ({picking.picking_type_id.id}) es uno de los tipos NO permitidos"
                _logger.warning(f"Zacalog: Syncer {msg}")
                picking.write({"x_status": 1})
                #self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, msg, "syncer", self.env['zacatrus_base.notifier'].LEVEL_WARNING)
                continue
            
            if not picking.picking_type_id.id in self.ALLOWED_OPERATION_TYPES:
                msg = f"{picking.name} {picking.picking_type_id.name} ({picking.picking_type_id.id}) no es uno de los tipos permitidos"
                _logger.warning(f"Zacalog: Syncer {msg}")
                self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, msg, "syncer", self.env['zacatrus_base.notifier'].LEVEL_WARNING)
            
            #if picking.state == 'confirmed' and picking.group_id:
            if picking.state != 'done' and picking.group_id:
                # En espera y con grupo de abastecimento
                groups = self.env['procurement.group'].search([('id', '=', picking.group_id.id)])
                for group in groups:
                    if not group.sale_id:
                        continue # Si viene de un abastecimiento sin venta, no procesamos los 'en espera'

            team = False
            if picking.picking_type_id.id in [3, 104]: #self.SEGOVIA_PICK_TYPE_ID, Distri: Pick
                if picking.sale_id:
                    team = picking.sale_id.team_id.id #6: web, 11: pickOp, 14: amazon, 13: zacatrus.fr
            
            if team in [6, 13]: #Already decreased in Magento
                if picking.state == 'cancel': # If it is a cancel, we have to return stock to Odoo manually
                    self._syncMagento(picking, True) # reverse = True (último parámetro)
                else:
                    picking.write({"x_status": 1})
            elif team in [14]: #Amazon: Lo de Amazon no se procesa porque la balda de amazon está fuera del stock
                picking.write({"x_status": 1})
            elif picking.state == 'cancel':
                picking.write({"x_status": 1}) #Todos los cancelados
            elif picking.picking_type_id.id in self.SEGOVIA_INTERNAL_TYPES:
                if picking.picking_type_id.id == 936 or picking.location_dest_id.id == 936: #AMAZON_LOCATION_ID
                    self._syncMagento(picking)
                else:
                    picking.write({"x_status": 1}) # Movimientos internos no se procesan en Segovia
            elif (picking.picking_type_id.id in Syncer.FROM_SHOP_DELIVERY_TYPE #Envíos que salen de tiendas
                and picking.location_dest_id.id != 10 #picking.INTER_COMPANY_LOCATION_ID
                #and not interShopMove
                ):
                if picking.sale_id:
                    if picking.sale_id['x_shipping_method'] not in ['zacaship', 'stock_pickupatstore']:
                        msg = f"Esto es un pedido que sale de tienda, pero no es ni una recogida ni un Trus ({picking.sale_id['x_shipping_method']})"
                        self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, msg, "syncer", self.env['zacatrus_base.notifier'].LEVEL_WARNING)
                else:                            
                    self._syncMagento(picking) # Salidas de tienda varias. Para movimiento entre tiendas por ejemplo

                    #if self.sale_id['x_shipping_method'] == 'zacaship':
                    #    self._syncGlovo(self, self.sale_id)                                
                    #if self.sale_id['x_shipping_method'] == 'stock_pickupatstore':
                    #    self._syncPickupatstore(self, picking.sale_id, picking)
            else:
                if picking.picking_type_id.id in [28]: #ferias #TODO: ¿por qué?
                    picking.write({"x_status": 1})
                else:
                    self._syncMagento(picking) #sincroniza cualquier otra cosa
                    
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
        dest = self.env['stock.location'].browse(picking.location_dest_id.id)
        parentLocationDestId = dest.location_id.id
        _from = self.env['stock.location'].browse(picking.location_id.id)
        parentLocationId = _from.location_id.id

        # Warehouse moves
        #shopLocations = Syncer.SHOP_RESERVE_LOCATIONS + Syncer.SHOP_LOCATIONS + [13, 1717]
        shopLocations = Syncer.SHOP_LOCATIONS + [13, 1717]
        if picking.location_dest_id.id in shopLocations or parentLocationDestId in [13, 1717]:#[13, 11, 1717, 1716]:
            #Al ser una entrada, hay que esperar a que el movimiento esté validado picking.state == 'done'
            if picking.state == 'done':
                out = False
                if not picking.location_dest_id.id in self.sourceCodes:
                    _logger.warning(f"Zacalog: Dest source not found.")
                    #sourceCode = "WH"
                else:
                    sourceCode = self.sourceCodes[picking.location_dest_id.id]
        elif picking.location_id.id in shopLocations or parentLocationId in [13, 1717]:
            #En las salidas, hay que descontarlo en cuanto se reserva.
            #TODO: Habría que ver qué hacer en el caso de cancelaciones y tal: Para subir nota.
            out = True
            if not picking.location_id.id in self.sourceCodes:
                _logger.warning(f"Zacalog: Source not found.")
                #sourceCode = "WH"
            else:
                sourceCode = self.sourceCodes[picking.location_id.id]
        else:
            msg = f"{picking.name} is not a warehouse move"
            #self.env['zacatrus_base.notifier'].notify('stock.picking', picking.id, msg, "syncer", self.env['zacatrus_base.notifier'].LEVEL_WARNING)
            _logger.warning(f"Zacalog: syncer: {msg}")
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
                    self.env['zacatrus.connector'].decreaseStock(product.default_code, o[qtyField], False, sourceCode, picking)
                else:
                    self.env['zacatrus.connector'].increaseStock(product.default_code, o[qtyField], picking.picking_type_id.id == 2, sourceCode, picking)
        
        picking.write({"x_status": 1})
        #self.getMagentoConnector().procStockUpdateQueue()

    def _syncPickupatstore(self, sale, picking):
        if sale['team_id'][0] == 6:
            sc = self.env['zacatrus_base.slack']
            channel = sc.getSlackChannelByLocation(picking.location_id.id)

            if picking.state in ['assigned', 'confirmed']: 
                if picking.x_status == 0:
                    sc.sendWarn(f"Ha llegado un nuevo pedido para recogida en tienda: {self.name} (#{sale.client_order_ref}). Por favor, prepáralo (en Odoo) y guárdalo en una bolsa hasta que vengan a buscarlo. Cuando termines aviso al cliente.", channel)
                    picking.write({"x_status": 601})
            elif picking.state == 'done' and picking.x_status in [601, 602, 607]:
                picking.write({"x_status": 603})
                try:
                    msg = f"No he conseguido avisar al cliente. Por favor, llama o manda un email para que pase a recoger su pedido ({sale.client_order_ref})."
                    if self.notifyCustomer(picking.sale_id):
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
                    self.env['zacatrus_base.notifier'].notify('sale.order', order.id, msg, "syncer", self.env['zacatrus_base.notifier'].LEVEL_ERROR)
                        
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

    def getStock(self, productId, location_s = None, mindReserved = False, mindChilds = True, mindAmazon = False):
        single = True
        if not location_s:
            location_s = [13]
        else:
            if not isinstance(location_s, list):
                location_s = [location_s]
            else:
                single = False

        qtys = {}
        for locationId in location_s:
            allLocations = [locationId]
            if locationId == 13 and mindChilds:
                for lid in [13, 938]: # Segovia, sotano
                    locations = self.env['stock.location'].browse(lid)
                    if mindAmazon:
                        try:
                            locations.remove(936) # Amazon
                        except:
                            pass
                    for location in locations:
                        allLocations += location.child_ids.ids

            if locationId == 1717 and mindChilds: #Distri
                for lid in [1717]:
                    locations = self.env['stock.location'].browse(lid)
                    for location in locations:
                        allLocations += location.child_ids.ids

            args = [('location_id', 'in', allLocations), ('product_id', '=', productId)] 
            quants = self.env['stock.quant'].search(args)
            qtys[locationId] = 0
            for quant in quants:
                qtys[locationId] += quant.quantity
                if mindReserved:
                    qtys[locationId] -= quant.reserved_quantity

            if single:
                return qtys[locationId]

        return qtys

    def fix(self, update = True, all = False):
        locationsToSync = self.SHOP_LOCATIONS + [13, 1717, 938] #SEGOVIA_LOCATION_ID, SEGOVIA_DISTRI_LOCATION_ID, SEGOVIA_SOTANO_ID

        args = [
            ('active','=',True),
            ('type', '=', 'product'),
            #('default_code', 'in', ['ALTDISBO01SP', 'MC48ES', 'MELMACGAMES-295895PACK']) 
        ] 
        if not all:
            moves = self.env['stock.move'].search( [ ('write_date', '>', datetime.datetime.now() - datetime.timedelta(hours = 24)) ] )
            productsToCheck = []
            for move in moves:
                if not move.product_id.id in productsToCheck:
                    productsToCheck.append(move.product_id.id)
            args.append( ('id', 'in', productsToCheck) )

        products = self.env['product.product'].search(args)
        #magento = self.getMagentoConnector()

        productsSkus = self.getProductsSkus()
        for odooProduct in products:
            odooStock = self.getStock(odooProduct['id'], locationsToSync, True, True, True) # Previsto / disponible
            odooStockReal = self.getStock(odooProduct['id'], locationsToSync, False, True, True) # Stock real
            magentoStock = False
            try:
                magentoStock = self.env['zacatrus.connector'].getStocks(odooProduct.default_code)
            except Exception as e:
                _logger.error(f"Zacalog: Unable to get stock from Magento for {odooProduct.default_code}")
            if odooStock and magentoStock:
                for stockLocation in locationsToSync:
                    if stockLocation in self.sourceCodes:
                        # No se actualiza cuando el stock real es ditinto del disponible para evitar tocar los movimientos que están en proceso
                        if odooStock[stockLocation] == odooStockReal[stockLocation]:
                            sourceCode = self.sourceCodes[stockLocation]
                            if magentoStock and not sourceCode in magentoStock:
                                magentoStock[sourceCode] = {"qty": 0}
                            if not stockLocation in odooStock:
                                odooStock[stockLocation] = 0  

                            if stockLocation == 13 and 938 in odooStock:
                                odooStock[stockLocation] += odooStock[938]

                            if odooProduct and odooProduct['default_code'] and magentoStock:
                                if magentoStock[sourceCode]['qty'] != odooStock[stockLocation]:
                                    saleable = self.env['zacatrus.connector'].getSalableQty(odooProduct['default_code'], sourceCode)
                                    if ( saleable >= 0 or sourceCode not in ['default', 'wh', 'WH', 'FR_TL']):
                                        if odooStock[stockLocation] > magentoStock[sourceCode]['qty']:
                                            if magentoStock[sourceCode]['qty'] >= 0: #exlude preorders
                                                if not self.isScheduledSale(odooProduct.default_code, productsSkus):
                                                    msg = f"^ {sourceCode} {odooProduct.default_code} ^ Mage:{magentoStock[sourceCode]['qty']} -> Odoo:{odooStock[stockLocation]}"
                                                    _logger.warning(f"Zacalog: {msg}")
                                                    self.env['zacatrus_base.notifier'].notify('product.product', odooProduct.id, msg, "fix-stock", self.env['zacatrus_base.notifier'].LEVEL_WARNING)
                                                    if update:
                                                        increase = odooStock[stockLocation] - magentoStock[sourceCode]['qty']
                                                        self.env['zacatrus.connector'].increaseStock(odooProduct.default_code, increase, False, sourceCode)

                                        if odooStock[stockLocation] < magentoStock[sourceCode]['qty']:
                                            if odooStock[stockLocation] < magentoStock[sourceCode]['qty']:
                                                decrease = magentoStock[sourceCode]['qty'] - odooStock[stockLocation]
                                                sku = odooProduct.default_code
                                                if not odooStock[stockLocation] < 0 and not self.isScheduled(sku, sourceCode):
                                                    msg = f"{sourceCode} {sku} v M:{magentoStock[sourceCode]['qty']} -> O:{odooStock[stockLocation]}"
                                                    _logger.warning(f"Zacalog: {msg}")
                                                    self.env['zacatrus_base.notifier'].notify('product.product', odooProduct.id, msg, "fix-stock", self.env['zacatrus_base.notifier'].LEVEL_WARNING)
                                                    if update:
                                                        self.env['zacatrus.connector'].decreaseStock(sku, decrease, False, sourceCode)

    def isScheduled(self, sku, source):
        args = [
            ('sku', '=', sku),
            ('forecast', '=', True),
            ('create_date', '>', datetime.datetime.now() - datetime.timedelta(days = 3)),  
            ('source', '=', source)
        ]
        queue = self.env['zacatrus_base.queue'].search(args)
        for item in queue:
            if item.picking_id.state not in ['cancel', 'done']:
                return True
        
        return False
    
    def getProductsSkus(self):
        productsSkus = []
        args = [
            ('picking_type_id', 'in', [3, 104]), # segovia, distri
            ('create_date', '>', datetime.datetime.now() - datetime.timedelta(days = 3)),
            ('state', 'not in', ['cancel', 'done']),
        ]
        productIds = []
        pickings = self.env['stock.picking'].search(args)
        for picking in pickings:
            margs = [
                ('picking_id', '=', picking.id)
            ]
            moves = self.env['stock.move'].search(margs)
            for move in moves:
                if move.product_id.id not in productIds:
                    productIds.append(move.product_id.id)
            
        if productIds:
            pargs = [
                ('id', 'in', productIds)
            ]
            products = self.env['product.product'].search(pargs)
            for product in products:
                if product.default_code not in productsSkus:
                    productsSkus.append(product.default_code)

        return productsSkus
                    
    def isScheduledSale(self, sku, productsSkus):   
        if sku in productsSkus:
            return True
        
        return False