import datetime, logging, csv, re
import zipfile, base64

_logger = logging.getLogger(__name__)

EDI_PARTNER = {
    5663: "8422416200508",
    5662: "8422416200621",
    5663: "8422416200560",
    5661: "8422416000016" #central
}

DISTRI_WAREHOUSE_ID = 21
DISTRI_TEAM_ID = 2
EDI_USER_ID = 127

class EdiTalker ():
    EDI_STATUS_INIT = 1
    EDI_STATUS_READY = 10
    EDI_STATUS_SENT = 20
    EDI_STATUS_INVOICED = 30

    def _due(line): #ERE1V
        data = {
            "counter": line[6:8].strip(),
            "timeRef": line[8:11].strip(),
            "timeRel": line[11:14].strip(),
            "periodType": line[14:17].strip(),
            "periodNumber": line[17:20].strip(),
            "date": line[20:28].strip(),
            "amount": line[28:46].strip(),
        }

        return data

    def _line(line): #ERE1T
        data = {
            "lineNumber": line[6:12].strip(),
            "barcode": line[12:27].strip(),
            "codeType": line[27:30].strip(),
            "idType": line[30:47].strip(),
            "desc1": line[47:117].strip(),
            "desc2": line[117:187].strip(),
            "productType": line[187:188].strip(),
            #"sellerProductNumber": line[188:223].strip(),
            "buyerProductNumber": line[223:258].strip(),
            "promoVariable": line[258:293].strip(),
            "additionalBarcode": line[293:328].strip(),
            "orderedQty": line[328:344].strip(),
            "promoQty": line[344:360].strip(),
            "uomCalificator": line[360:366].strip(),
            "unitsPerBox": line[366:382].strip(),
            "time1Calificator": line[382:385].strip(),
            "time1": line[385:397].strip(),
            "time2Calificator": line[397:400].strip(),
            "time2": line[400:412].strip(),
            "lineBase": line[412:430].strip(),
            "unitGrossPrice": line[430:446].strip(),
            "unitBasePrice": line[446:462].strip(),
            "priceInfo": line[462:478].strip(),
            "uomCalificator": line[478:484].strip(),
            "VATCalificator": line[484:490].strip(),
            "VATPerc": line[490:496].strip(),
            "VATAmount": line[496:514].strip(),
            "REPerc": line[514:520].strip(),
            "REAmount": line[520:538].strip(),
            "otherTaxCalificator": line[538:544].strip(),
            "otherTaxPerc": line[544:550].strip(),
            "otherTaxAmount": line[550:568].strip(),
            "netWeigh": line[568:586].strip(),
            "uomWeighCalificator": line[586:592].strip(),
            "modelDescription": line[592:617].strip(),
            #"color": line[617:642].strip(),
            "size": line[642:667].strip(),
            "size": line[667:692].strip(),
            "format": line[692:727].strip(),
            "buyerGroupCode": line[727:762].strip(),
            "serialNumber": line[762:797].strip(),
            "manufacturerNumber": line[797:832].strip(),
            "bundleNumber": line[832:835].strip(),
            "time3Calificator": line[835:847].strip(),
            "time3": line[847:865].strip(),
            "lineAmountWithTax": line[865:874].strip(),
            "baseNetPrice": line[874:890].strip(),
            "basePriceWithTax": line[890:899].strip(),
            "shipmentSlipNumber": line[899:916].strip(),
            "shipmentSlipDate": line[916:928].strip(),
            "finalClientCode": line[928:945].strip(),
            "finalClientName": line[945:1015].strip(),
            "finalClientAddress": line[1015:1085].strip(),
            "finalClientCity": line[1085:1120].strip(),
            "finalClientZip": line[1120:1129].strip(),
            "itemId": line[1129:1144].strip(),
        }


        return data

    def _tax(line): #ERE1I
        data = {
            "lineNumber": line[6:8].strip(),
            "calificator": line[8:14].strip(),
            "perc": line[14:20].strip(),
            "amount": line[20:38].strip(),
            "base": line[38:56].strip(),
        }

        return data

    def _partner(line): #ERE1T
        data = {
            "calificator": line[6:9].strip(),
            "code": line[9:26].strip(),
            "agencyCode": line[26:29].strip(),
            "name1": line[29:64].strip(),
            "name2": line[64:99].strip(),
            "name3": line[99:134].strip(),
            "name4": line[134:169].strip(),
            "name5": line[169:204].strip(),
            "address1": line[204:239].strip(),
            "address2": line[239:274].strip(),
            "address3": line[274:309].strip(),
            "address4": line[309:344].strip(),
            "city": line[344:379].strip(),
            "province": line[379:388].strip(),
            "zip": line[388:397].strip(),
            "countryCode": line[397:400].strip(),
            "ref1Calificator": line[400:403].strip(),
            "ref1": line[403:438].strip(),
            "contactFunction": line[438:441].strip(),
            "contactId": line[441:458].strip(),
            "department": line[458:493].strip(),
            "refCalificator": line[493:496].strip(),
            "ref": line[496:513].strip(),
        }

        return data

    def _textInfo(line): #ERE1T
        data = {
            "calificator": line[6:12].strip(),
            "text1": line[12:82].strip(),
            "text2": line[82:152].strip(),
            "text3": line[152:222].strip(),
            "text4": line[222:292].strip(),
            "text5": line[292:362].strip(),
        }
        return data
    
    def _procGlobalData(line): #ERE1C
        lineType = line[:6].strip()
        data = {
            "docType": line[6:9].strip(),
            "orderNumber": line[9:26].strip(),
            "function": line[26:29].strip(),
            "time": line[29:41].strip(),
            "calificator1": line[41:44].strip(),
            "time1": line[44:56].strip(),
            "calificator2": line[56:59].strip(),
            "time2": line[59:71].strip(),
            "additionalInfo": line[71:74].strip(),
            "openOrderNumber": line[74:91].strip(),
            "priceListNumber": line[91:108].strip(),
            "supplierOrderNumber": line[108:125].strip(),
            "additionalReferenceCalificator": line[125:128].strip(),
            "additionalReferenceNumber": line[128:145].strip(),
            "currencyCode": line[145:148].strip(),
            "dueTime": line[148:156].strip(),
            "shipmentPaymentType": line[156:159].strip(),
            "deliveryConditions": line[159:162].strip(),
            "baseTotal": line[162:180].strip(),
            "discountTotal": line[180:198].strip(),
            "base": line[198:216].strip(),
            "taxes": line[216:234].strip(),
            "totalToPay": line[234:252].strip(),
            "grossTotal": line[252:270].strip(),
            "sas": line[270:287].strip(),
        }
        return data

    def _procHeader(line): #RECTL
        lineType = line[:6].strip()
        msgType = line[6:12].strip()
        if msgType != "ORDERS":
            raise WrongFileException('This is not an order.')
        header = {
            "msgType": line[6:12].strip(),
            "issuerCode": line[12:47].strip(),
            "receiverCode": line[47:82].strip(),
            "shipmentId": line[82:122].strip(),
            "time": line[122:134].strip(),
        }
        return header

    def readBuffer(buffer):      
        info = []
        partner = []
        tax = []
        due = []
        productLine = []
        idx = 0
        orders = []
        header = None
        data = None
        order = {}
        for line in buffer.splitlines():
            lineType = line[:6].strip()
            #print (line)
            if lineType == "RECTL":
                header = EdiTalker._procHeader(line)
            if lineType == "ERE1C":
                if idx > 0:
                    order["header"] = header
                    order["data"] = globalData
                    order["info"] = info
                    order["partner"] = partner
                    order["tax"] = tax
                    order["due"] = due
                    order["line"] = productLine
                    orders.append(order)

                    info = []
                    partner = []
                    tax = []
                    due = []
                    productLine = []
                    order = {}
                    data = None

                idx += 1
                globalData = EdiTalker._procGlobalData(line)
            if lineType == "ERE1T":
                data = EdiTalker._textInfo(line)
                info.append( data )
            if lineType == "ERE1P":
                data = EdiTalker._partner(line)
                partner.append(data)
            if lineType == "ERE1I":
                data = EdiTalker._tax(line)
                tax.append(data)
            if lineType == "ERE1V":
                data = EdiTalker._due(line)
                due.append(data)
            if lineType == "ERE1L":
                data = EdiTalker._line(line)
                productLine.append(data)

        order["header"] = header
        order["data"] = globalData
        order["info"] = info
        order["partner"] = partner
        order["tax"] = tax
        order["due"] = due
        order["line"] = productLine
        orders.append(order)

        return orders

    def getPickingFromOrder(env, order):
        args = [
            ('sale_id', '=', order['id']),
            ('picking_type_id', '=', 103), # Distri ordenes de entrega
            ('state', '=', 'done'),
        ]
        pickings = env['stock.picking'].search_read(args)
        for picking in pickings:
            return picking

        raise Exception("Pedido no encontrado: " + str(order['name']))

    def getPickingLinesFromOrderId(env, order_id):
        args = [('order_id', '=', order_id)]
        lines = env['sale.order.line'].search_read(args)
        
        return lines
    
    def loadProduct(env, product_id):
        args = [('id', '=', product_id)]
        products = env['product.product'].search_read(args)

        for product in products:
            return product
    
    def getGLNFromPartnerId(env, partner_id):
        args = [
            ('id', '=', partner_id)
        ]
        partners = env['res.partner'].search_read(args)
        for partner in partners:
            return partner

        raise Exception("wrong client")
    
    def writeEncoded(line, writeReturn = True):
        #_line = formatString.format(line.decode('utf8').encode('iso-8859-1'))
        char_to_replace = {'Á': 'A','É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U'}
        for key, value in char_to_replace.items():
            line = line.replace(key, value)

        #file.write( line )
        if writeReturn:
            line += "\n"

        return line

    def _getHeader(shipmentId, mode, partnerGLN):
        now = datetime.datetime.now()

        #if mode == 'INVOIC':
        #    _id = str(10000000000 + int(shipmentId))
        #else:
        #    _id = shipmentId


        line = '{:<6}'.format('RECTL')
        line = line + '{:<6}'.format( mode )
        line = line + '{:<35}'.format('B86133188') # ES este nuestro GLN_PROVEEDOR ?????
        line = line + '{:<35}'.format( partnerGLN )
        line = line + '{:<40}'.format( shipmentId )
        line = line + '{:<12}'.format(now.strftime("%Y%m%d%H%M"))

        return line
    
    def _getGlobalData(picking, shipmentId, orderId):
        now = datetime.datetime.now()
        #oday = datetime.date.fromtimestamp(time.time())
        deliveryDate = now + datetime.timedelta(days=3)

        line = '{:<6}'.format('SEH1C')
        line = line + '{:<6}'.format('351')
        line = line + '{:<17}'.format(shipmentId)
        line = line + '{:<6}'.format('9')
        line = line + '{:<12}'.format(now.strftime("%Y%m%d%H%M"))
        line = line + '{:<12}'.format(deliveryDate.strftime("%Y%m%d%H%M")) # Fecha prevista de entrega
        line = line + '{:<3}'.format('') # empty
        line = line + '{:<12}'.format('') # empty
        line = line + '{:<3}'.format('') # empty
        line = line + '{:<12}'.format('') # empty
        line = line + '{:<6}'.format('') # empty
        line = line + '{:<17}'.format( orderId ) # debe de ser el número de pedido EDI?
        line = line + '{:<12}'.format('') # empty
        line = line + '{:<17}'.format(shipmentId)
        line = line + '{:<12}'.format(now.strftime("%Y%m%d%H%M"))
        line = line + '{:<3}'.format('AAK')
        line = line + '{:<17}'.format('') #Numero de aviso de expedición que reemplazamos. Obligatorio si BGM.,1225=5
        line = line + '{:<12}'.format('')
        line = line + '{:<3}'.format('AAK')
        line = line + '{:<17}'.format('')
        line = line + '{:<12}'.format('')
        line = line + '{:<3}'.format('')
        line = line + '{:<3}'.format('')
        line = line + '{:<70}'.format('')
        line = line + '{:<3}'.format('')
        line = line + '{:<13}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<17}'.format('')
        line = line + '{:<17}'.format('')
        line = line + '{:<70}'.format('')

        return line

    def _getPartner(env, picking, atype, partner_id):
        line = '{:<6}'.format('SEH1D')
        line = line + '{:<3}'.format(atype)
        if partner_id in EDI_PARTNER:
            gln = EDI_PARTNER[partner_id]
        else:
            if isinstance(partner_id, str):
                gln = partner_id
            else:
                try:
                    _partner = EdiTalker.getGLNFromPartnerId(env, partner_id)
                    gln = _partner["ref"]
                except Exception as e:
                    gln = partner_id
        line = line + '{:<17}'.format( gln )
        line = line + '{:<3}'.format('9')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<9}'.format('')
        line = line + '{:<9}'.format('')
        line = line + '{:<3}'.format('')
        if atype == 'BY' or atype == 'DP':
            line = line + '{:<3}'.format('API')
            line = line + '{:<35}'.format('831')
        else:
            line = line + '{:<3}'.format('')
            line = line + '{:<35}'.format('')
        line = line + '{:<3}'.format('')
        line = line + '{:<17}'.format('')

        return line

    def _getBundles(picking, idx, sscc = False):
        line = '{:<6}'.format('SEH1P')
        line = line + '{:<12}'.format( idx )
        if idx == 1:
            line = line + '{:<12}'.format('') 
        else:
            line = line + '{:<12}'.format(str(idx - 1))
        packages = 1
        if idx == 3 and picking['number_of_packages']:
            packages = picking['number_of_packages']
        line = line + '{:<8}'.format( packages ) # número de paquetes (BULTOS)
        line = line + '{:<6}'.format('')
        line = line + '{:<6}'.format('')
        code = ''
        if idx == 1:
            code = '201'
        if idx == 2:
            code = 'BE'
        if idx == 3:
            code = 'CT'
        line = line + '{:<6}'.format(code)
        line = line + '{:<35}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:18}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:16}'.format('')
        line = line + '{:6}'.format('')
        line = line + '{:70}'.format('')
        line = line + '{:35}'.format('')
        line = line + '{:35}'.format('')
        line = line + '{:35}'.format('')
        line = line + '{:35}'.format('')

        if sscc:
            line = line + '{:35}'.format(EdiTalker._generateSSCC( sscc )) #sscc
        else:
            line = line + '{:35}'.format('') #sscc

        return line

    def _getCD(number):
        even = False
        calc = 0
        for pos in range (0, len(number)):
            multipler = 0
            if even:
                multipler = 1
            else:
                multipler = 3

            even = not even
            calc = calc + int(number[pos]) * multipler

        return (10 - (calc % 10)) % 10

    def _generateSSCC(number):
        # Ej.: 986133180000011054
        ret = "98613318" + '{0:09}'.format( int(number) )
        return ret + str(EdiTalker._getCD( ret ))

    def _getLines(env, picking, orderNumber, lineNumber, buyerProductNumber):
        product = EdiTalker.loadProduct( env, picking['product_id'][0] )

        line = '{:<6}'.format('SEH1L')
        line = line + '{:<6}'.format( str(lineNumber) )
        line = line + '{:<15}'.format( str(product['barcode']) )
        line = line + '{:<70}'.format( str(product['name'])[:70] )
        line = line + '{:<7}'.format( '' )
        line = line + '{:<15}'.format( str(product['barcode']) ) #sku
        line = line + '{:<15}'.format( '' )
        line = line + '{:<15}'.format( '' )
        line = line + '{:<15}'.format( '' )
        line = line + '{:<35}'.format( '' )
        line = line + '{:<15}'.format( buyerProductNumber ) #Número de articulo del comprador (IN)
        line = line + '{:<16}'.format( str('{0:.3f}'.format( (picking['product_qty']) )) )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<16}'.format( '1' ) # UC Unidades de consumo en unidad de expedición
        line = line + '{:<12}'.format( '' )
        line = line + '{:<6}'.format( 'ON' )
        line = line + '{:<17}'.format( orderNumber ) # Número de pedido
        line = line + '{:<12}'.format( '' )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<17}'.format( '' )
        line = line + '{:<12}'.format( '' )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<17}'.format( '' )
        line = line + '{:<12}'.format( '' )
        line = line + '{:<16}'.format( '' )
        line = line + '{:<15}'.format( '' )
        line = line + '{:<16}'.format( '' )
        line = line + '{:<3}'.format( '' )
        line = line + '{:<16}'.format( '' )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<35}'.format( '' )
        line = line + '{:<35}'.format( '' ) 
        line = line + '{:<6}'.format( lineNumber ) # Número de línea del pedido
        line = line + '{:<6}'.format( '' )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<16}'.format( '' )
        line = line + '{:<3}'.format( '' )
        line = line + '{:<18}'.format( '' )
        line = line + '{:<18}'.format( '' )
        line = line + '{:<3}'.format( '' )
        line = line + '{:<18}'.format( '' )
        line = line + '{:<18}'.format( '' )
        line = line + '{:<3}'.format( '' )
        #print line
        #sys.exit(0)
        #print product
        return line
    
    def savePickingsToSeres(env, order):#, original_order, path, bundleName, upload = False):
        picking = EdiTalker.getPickingFromOrder( env, order )

        orderNumber = order["x_edi_order"]
        data = EdiTalker.getGLNFromPartnerId(env, order['partner_invoice_id']['id'])

        #file = open(fileName,"w") 

        line = ""
        line += EdiTalker.writeEncoded(EdiTalker._getHeader( order["x_edi_shipment"], 'DESADV', data["ref"]) )
        line += EdiTalker.writeEncoded(EdiTalker._getGlobalData(picking, order["x_edi_shipment"], orderNumber)  )
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(env, picking, 'MS', 'B86133188')  ) # Emisor
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(env, picking, 'SU', 'B86133188')  ) # Receptor del mensaje
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(env, picking, 'MR', order['partner_invoice_id']['id'])  ) # Receptor del mensaje
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(env, picking, 'IV', order['partner_invoice_id']['id'])  ) # Receptor del mensaje 
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(env, picking, 'DP', order['partner_shipping_id']['id'])  ) # Almacén 5663 por ejemplo
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(env, picking, 'BY', order["partner_id"]['id'])  ) # Tienda compradora (destino final - viene del EDI del pedido)

        #logistics
        ssccNumber = str(order['id']).zfill(9) #TODO: revisar

        line += EdiTalker.writeEncoded(EdiTalker._getBundles(picking, 1)  )
        line += EdiTalker.writeEncoded(EdiTalker._getBundles(picking, 2)  )
        line += EdiTalker.writeEncoded(EdiTalker._getBundles(picking, 3, ssccNumber)  )

        lines = EdiTalker.getPickingLinesFromOrderId(env, order['id'])
        for aline in lines:
            if aline['product_id'][0] == 186797:
                done = True
            else:
                product = EdiTalker.loadProduct(env, aline['product_id'][0])
                done = False
                #for ori_line in original_order['line']:
                    #if (int(ori_line["barcode"]) == int(product["barcode"])):
                lineNumber = aline['x_edi_line'] #ori_line['lineNumber']
                buyerProductNumber = aline['x_edi_product']
                l = EdiTalker._getLines(env, aline, order["x_edi_shipment"], lineNumber, buyerProductNumber)
                line += EdiTalker.writeEncoded( l  )
                
        return line

    def createOrRetrieveECIClient(env, aPartner):
        args = [('ref', '=', aPartner["code"])] #query clause
        partners = env['res.partner'].search_read(args)
        for partner in partners:
            return partner['id']
        
        raise Exception("Zacalog: EDI: No tenemos cliente creado para este código: "+ aPartner["code"]) # we don't create it anymore
        
    
    def deleteError(env, ediOrder):
        from .BundleWizard import BundleWizard
        bundle = BundleWizard.getCurrentBundle(env)
        args = [
            ('origin', '=', ediOrder['data']['orderNumber']),
            ('bundle_id', '=', bundle['id']),
        ]
        env['zacaedi.error'].search( args ).unlink()

    def saveError(env, code, ediOrder, msg):
        from .BundleWizard import BundleWizard
        bundle = BundleWizard.getCurrentBundle(env)
        args = [
            ('origin', '=', ediOrder['data']['orderNumber']),
            ('bundle_id', '=', bundle['id']),
        ]
        count = env['zacaedi.error'].search_count( args )
        if count == 0:
            error = env['zacaedi.error'].create({
                'origin': ediOrder['data']['orderNumber'],
                'code': code,
                'message': f"Pedido {ediOrder['data']['orderNumber']}: {msg}",
                'bundle_id': bundle['id']
            })
    
    def createSaleOrderFromEdi(env, ediOrder):
        #userId = 127

        invoicingPartner = ""
        shippingPartner = False
        buyerPartner = False
        try:
            for partner in ediOrder['partner']:
                if partner ['calificator'] == "IV":
                    invoicingPartner = EdiTalker.createOrRetrieveECIClient( env, partner )
                if partner ['calificator'] == "DP":
                    shippingPartner = EdiTalker.createOrRetrieveECIClient( env, partner )
                if partner ['calificator'] == "BY":
                    buyerPartner = EdiTalker.createOrRetrieveECIClient( env, partner )
                #print (partner)
        except Exception as e:
            EdiTalker.saveError(env, 101, ediOrder, str(e))
            raise e


        if invoicingPartner not in [5661, 5967, 5758]: # ECI, Juguettos, Fnac
            EdiTalker.saveError(env, 102, ediOrder, "No es ninguno de los clientes de EDI.")
            raise Exception(f"wrong client {invoicingPartner}")

        if not shippingPartner:
            EdiTalker.saveError(env, 103, ediOrder, "Dirección de envío incorrecta.")
            raise Exception("wrong shipping address")
      
        args = [('client_order_ref', '=', ediOrder['data']['orderNumber'])]
        dups = env['sale.order'].search(args)
        if len(dups) > 0:
            EdiTalker.saveError(env, 104, ediOrder, "Este pedido ya está creado.")
            raise Exception(f"Order already processed: {ediOrder['data']['orderNumber']}")

        _order = {
            'partner_id': buyerPartner,
            'partner_invoice_id': invoicingPartner,
            'partner_shipping_id': shippingPartner,
            'date_order': datetime.date.today().strftime("%Y-%m-%d"),
            #'location_id': DISTRI_LOCATION_ID, #self.locations[self.myEnv]["out"],
            'warehouse_id': DISTRI_WAREHOUSE_ID,
            'pricelist_id': 6,
            'client_order_ref': ediOrder['data']['orderNumber'],
            'origin': ediOrder['header']['shipmentId'],
            'state': 'draft',
            'team_id': DISTRI_TEAM_ID,
            'payment_term_id': 5,
            'user_id': EDI_USER_ID,
            'x_edi_order': ediOrder['data']['orderNumber'],
            'x_edi_shipment': ediOrder['header']['shipmentId'],
            'x_edi_status': EdiTalker.EDI_STATUS_INIT
        }
        createdOrder = env['sale.order'].create(_order)

        partners =  env['res.partner'].search_read( [ ('id', '=', invoicingPartner) ], ['property_product_pricelist'] )
        priceListItems = None;
        for partner in partners:
            if "property_product_pricelist" in partner and partner["property_product_pricelist"]:
                pricelistId = partner ["property_product_pricelist"][0]
                pliargs = [('pricelist_id', '=', pricelistId)]
                priceListItems =  env['product.pricelist.item'].search_read(pliargs, [])

        for item in ediOrder['line']:
            #print(item)
            args = [('barcode', '=', str(int(item['barcode'])))]
            fields = ['name', 'categ_id', 'default_code']
            products =  env['product.product'].search_read(args, fields)
            if len(products) == 0:
                EdiTalker.saveError(env, 105, ediOrder, "El producto con código de barras {item['barcode']} no existe.")
                raise Exception(f"Product not found with barcode {item['barcode']}.")

            onlyVirus = True
            for product in products:
                if product["default_code"] not in ['TRANVR2', 'TRG-025hal', 'TRG-025hal-EXP', 'Virus']:
                    onlyVirus = False

            #print("onlyVirus: "+ str(onlyVirus))

            for product in products:
                #print (product)
                discount = 0
                if priceListItems: # and float(item['unitGrossPrice']) == 0:
                    for plitem in priceListItems:
                        if "categ_id" in plitem  and plitem["categ_id"] and product["categ_id"][0] == plitem["categ_id"][0]:
                            discount = plitem['percent_price']
                if onlyVirus and discount > 38 and invoicingPartner == 5967: #OJO: solo Juguettos (5967)
                    discount = 38

                #print item['barcode']
                taxes = [1] # IVA21
                order_line = {
                    'order_id': createdOrder['id'],
                    'name': product['name'],
                    'product_uom_qty': item['orderedQty'],   
                    #'type': 'make_to_stock',
                    #'notes': '',
                    #'date_planned': datetime.date.today().strftime("%Y-%m-%d"),
                    'tax_id': [(6, 0, taxes)],
                    "product_id": product["id"],
                    "x_edi_line": item['lineNumber'],
                    "x_edi_product": item['buyerProductNumber']
                }
                if not discount: #float(item['unitGrossPrice']) != 0:
                    raise Exception(f"Edi error: Producto sin tarifa asignada {product['name']} ({product['default_code']})")
                    order_line['price_unit'] = item['unitGrossPrice']
                    # TODO: Fnac pone el GrossPrice sin descuento (a diferencia de ECI que lo pone con descuento);
                    # Así que en Fnac deberíamos tomar el campo unitBasePrice que ya viene con el 40% descontado
                    # Se puede discriminar por el id del cliente en Odoo (Fnac: 5758)
                    # OJO: La forma correcta y universal de hacerlo, sería utilizar siempre nuestra tarifa
                elif discount:
                    order_line['discount'] = discount

                lineId =  env['sale.order.line'].create(order_line)

        return createdOrder
    

    def _generateCSVs(env, orders, bundleId):
        #path= f"bundle{bundleId}"
        #oOdersIDs = []
        #for orderId in bundle["orders"]:
        #    orders = db.orders.find({"_id": orderId})
        #    for order in orders:
        #        oOdersIDs.append(int(order["odoo_order_id"]))
        count = {}
        for oOrder in orders:
            regExp = ',[ ]*([0-9]+)[ ]*-'
            m = re.search(regExp, oOrder["partner_shipping_id"][1])
            client = re.search(regExp, oOrder["partner_id"][1])
            if m:
                if client:
                    destCode = m.group(1)
                    clientCode = client.group(1)

                    fileName = f"B86133188_1010997_{destCode}"
                    if not fileName in count:
                        count[fileName] = 0
                    with open(f"{fileName}.csv", mode='w' if count[fileName] == 0 else 'a') as abstractFile:
                        abstractwriter = csv.writer(abstractFile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        if (count[fileName] == 0):
                            abstractwriter.writerow([
                                'Proveedor', 'Empresa Recepción','Lugar Recepción', 'Empresa Destino', 'Lugar destino','Uneco',
                                'Pedido','Albarán', 'Bultos','Embalaje', 'Transportista', 'Expedición'
                            ])
                        count[fileName] += 1
                        abstractwriter.writerow([
                            1010997, 
                            1, # Empresa de recepción
                            int(destCode), # Lugar de recepción
                            1, # Empresa destino
                            int(clientCode), #Lugar destino
                            831, #Uneco
                            int(oOrder["client_order_ref"]), #pedido
                            int(oOrder["origin"]), # albarán
                            1, # Bultos
                            'b', # Embalaje. 'b': Caja/bulto
                            'Transportes Nieto, S.L.', # Transportista
                            '0' # Expedición
                        ])
                else:
                    _logger.error( f"Zacalog: EDI: No client code in {oOrder['partner_id'][1]} in order {oOrder['client_order_ref']}." )
            else:
                _logger.error( f"Zacalog: EDI: No dest. code in {oOrder['partner_shipping_id'][1]} in order {oOrder['client_order_ref']}." )

        #Loop over all files to add TOTAL LINEAS
        for fileName in count:
            with open(f"{fileName}.csv", mode='a') as abstractFile:
                abstractwriter = csv.writer(abstractFile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                abstractwriter.writerow([
                    '', '', '', '', '', '', '', '', '', '', 
                    'TOTAL LINEAS',
                    count[fileName]
                ])

        zipf = zipfile.ZipFile(f"bundle{bundleId}.zip", 'w', zipfile.ZIP_DEFLATED)

        _logger.info( f"Zacalog: EDI: zip creado bundle{bundleId}.zip." )

        for fileName in count:
            zipf.write(f"{fileName}.csv", f"{fileName}.csv")
        zipf.close()
            
        with open(f"bundle{bundleId}.zip", mode="rb") as f:
            data = f.read()
            return base64.b64encode(data)

    def getInvoiceFromOrder(env, order):
        args = [
            ('invoice_origin', '=', order["display_name"]),
            ('state', '=', 'posted'),
        ]
        invoices = env['account.move'].search_read(args)
        for invoice in invoices:
            return invoice
        
        raise Exception(f"El pedido {order['name']} no tiene factura creada")

    def _getInvoiceData(invoice, order):
        if not invoice['invoice_date']:
            raise Exception(f"La factura del pedido {invoice['invoice_origin']} no tiene la fecha. ¿La habéis confirmado?")

        now = datetime.datetime.now()

        line = '{:<6}'.format('SINCC')
        line = line + '{:<6}'.format( '380' ) # tipo Factura comercial
        line = line + '{:<17}'.format(invoice['name']) # N. Factura
        line = line + '{:<6}'.format( '9' ) # tipo Factura comercial
        #print (invoice)
        line = line + '{:<8}'.format(str(invoice['invoice_date']).replace("-", "")) # F. Factura
        line = line + '{:<16}'.format( '' ) # Fecha del albarán
        line = line + '{:<6}'.format('60') # Modo de pago: Pagaré
        line = line + '{:<3}'.format('') 
        line = line + '{:<3}'.format('') 
        line = line + '{:<17}'.format( order['x_edi_order'] ) # N. Pedido
        line = line + '{:<17}'.format( order['x_edi_shipment'] ) #N. Albarán

        line = line + '{:<3}'.format('') 
        line = line + '{:<17}'.format('') 

        line = line + '{:<17}'.format('') 
        line = line + '{:<17}'.format('') 

        line = line + '{:<6}'.format('EUR')
        line = line + '{:<8}'.format(str(invoice['invoice_date_due']).replace("-", "")) 
        line = line + '{:<18}'.format('{0:.3f}'.format( invoice['amount_untaxed'] ))
        line = line + '{:<18}'.format('{0:.3f}'.format( invoice['amount_untaxed'] ))  # Base imponible
        line = line + '{:<18}'.format('{0:.3f}'.format( invoice['amount_untaxed'] ))  # Importe bruto
        line = line + '{:<18}'.format('{0:.3f}'.format( invoice['amount_tax'] ))  
        line = line + '{:<18}'.format('{0:.3f}'.format( invoice['amount_total_signed'] ))  
        line = line + '{:<18}'.format('')  
        line = line + '{:<18}'.format('')  
        line = line + '{:<18}'.format('')  
        line = line + '{:<16}'.format('')  
        line = line + '{:<8}'.format('')

        line = line + '{:<12}'.format(now.strftime("%Y%m%d"))
        line = line + '{:<17}'.format('')

        return line

    def _getInvoicePartner(env, invoice, atype, partner_id):
        line = '{:<6}'.format('SINCP')
        line = line + '{:<3}'.format(atype)
        _partner = EdiTalker.getGLNFromPartnerId(env, partner_id)
        gln = _partner["ref"]

        line = line + '{:<17}'.format( gln )
        line = line + '{:<3}'.format('9')
        line = line + '{:<35}'.format(_partner['name'][:35])
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format(_partner['street'][:35])
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format(_partner['city'][:35])
        if _partner['state_id']:
            _state = _partner['state_id'][1]
        else:
            _state = ''
        line = line + '{:<9}'.format( _state[:9] )
        line = line + '{:<9}'.format(_partner['zip'])
        line = line + '{:<3}'.format('')
        line = line + '{:<35}'.format(_partner['vat'][:35])
        line = line + '{:<35}'.format(831)
        line = line + '{:<3}'.format('')
        line = line + '{:<17}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<70}'.format('')
        line = line + '{:<35}'.format('')
        line = line + '{:<3}'.format('')
        line = line + '{:<35}'.format('')

        return line
    
    def getInvoiceLines(env, invoice_id):
        args = [('move_id', '=', invoice_id)]
        return env['account.move.line'].search_read(args)

    def _getInvoiceLine(env, _line, orderNumber, lineNumber, buyerProductNumber):
        product = EdiTalker.loadProduct(env, _line['product_id'][0] )

        line = '{:<6}'.format('SINCL')
        line = line + '{:<6}'.format( str(lineNumber) )
        line = line + '{:<15}'.format( str(product['barcode']) )
        line = line + '{:<35}'.format( str(product['name'])[:35] )
        line = line + '{:<1}'.format( 'M' )
        line = line + '{:<15}'.format( str(product['barcode']) ) #sku
        line = line + '{:<15}'.format( buyerProductNumber ) #Número de articulo del comprador (IN)
        line = line + '{:<15}'.format( '' )
        line = line + '{:<15}'.format( '' )
        line = line + '{:<15}'.format( '' )
        line = line + '{:<16}'.format( str('{0:.3f}'.format( int(_line['product_qty']) )) )
        line = line + '{:<16}'.format( '' )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<16}'.format( '' )
        line = line + '{:<16}'.format( '' )

        line = line + '{:<18}'.format( str('{0:.3f}'.format( _line['price_subtotal'] )) )
        _unitPrice = float( int(_line['price_subtotal'] * 1000 / _line['product_qty']) ) / 1000
        line = line + '{:<16}'.format( str('{0:.3f}'.format( _unitPrice )) )
        line = line + '{:<16}'.format( str('{0:.3f}'.format( _unitPrice )) )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<6}'.format( 'VAT' )
        vatAmount = 21
        line = line + '{:<6}'.format( str('{0:.3f}'.format( vatAmount )) )
        line = line + '{:<18}'.format( str('{0:.3f}'.format( _line['price_subtotal'] * vatAmount/100 )) )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<18}'.format( '' )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<6}'.format( '' )
        line = line + '{:<18}'.format( '' )
        line = line + '{:<17}'.format( '' )
        line = line + '{:<17}'.format( orderNumber ) #N. Albarán

        return line

    def _getInvoiceTax(idx, invoice):
        line = '{:<6}'.format('SINCI')
        line = line + '{:<2}'.format( idx )
        line = line + '{:<6}'.format( 'VAT' )
        vatAmount = 21
        line = line + '{:<6}'.format( str('{0:.3f}'.format( vatAmount )) )
        line = line + '{:<18}'.format( str('{0:.3f}'.format( invoice['amount_tax'] ))) #Impuesto
        line = line + '{:<18}'.format( str('{0:.3f}'.format( invoice['amount_untaxed'] ))) #Base

        return line
    
    def saveInvoicesToSeres(env, order, direct = False):
        if order["state"] != 'cancel':
            invoice = EdiTalker.getInvoiceFromOrder( env, order )
            partner = EdiTalker.getGLNFromPartnerId(env, order['partner_invoice_id']['id'])
            if direct:
                if not partner or not 'ref' in partner or not partner['ref'] or partner['ref'] == '':
                    raise Exception("Edi partner error sending invoice")
                shippingPartner = EdiTalker.getGLNFromPartnerId(env, order['partner_shipping_id']['id'])
                if not shippingPartner or not 'ref' in shippingPartner or not shippingPartner['ref'] or shippingPartner['ref'] == '':
                    raise Exception("Edi partner error sending invoice")

            line = ""
            line += EdiTalker.writeEncoded(EdiTalker._getHeader( order['x_edi_shipment'], 'INVOIC', partner['ref'] ))
            line += EdiTalker.writeEncoded(EdiTalker._getInvoiceData( invoice, order )  )

            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'II', 1)  ) # Emisor 1 = Zacatrus
            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'SU', 1)  ) # Proveedor
            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'SCO', 1)  ) # Proveedor
            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'IV', order['partner_invoice_id']['id'])  ) 
            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'PR', order['partner_invoice_id']['id'])  ) 
            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'BCO', order['partner_invoice_id']['id'])  ) 
            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'BY', order["partner_id"]['id'])  ) # Tienda compradora (destino final - viene del EDI del pedido)
            line += EdiTalker.writeEncoded(EdiTalker._getInvoicePartner(env, invoice, 'DP', order['partner_shipping_id']['id'])  ) # Almacén 5663 por ejemplo

            lines = EdiTalker.getPickingLinesFromOrderId(env, order['id'])
            idx = 0
            for aline in lines:
                idx += 1
                #print (line)
                if aline['product_id']:
                    #product = EdiTalker.loadProduct(env, line['product_id'][0])
                    if direct:
                        lineNumber = str(idx)
                        l = EdiTalker._getInvoiceLine(env, line, order['x_edi_shipment'], str(idx), "")
                        line += EdiTalker.writeEncoded(l)
                    else:
                        done = False
                        if aline['product_id'][0] == 186797: # Se filtra DHL para evitar errores
                            done = True
                        else:
                            l = EdiTalker._getInvoiceLine(env, aline, order['x_edi_shipment'], aline['x_edi_line'], aline['x_edi_product'])
                            line += EdiTalker.writeEncoded(  l  )
                                    
            l = EdiTalker._getInvoiceTax( 1, invoice )
            line += EdiTalker.writeEncoded( l  )

        return line
    
class WrongFileException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)