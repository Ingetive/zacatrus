import datetime, logging

_logger = logging.getLogger(__name__)

EDI_PARTNER = {
    5663: "8422416200508",
    5662: "8422416200621",
    5663: "8422416200560",
    5661: "8422416000016" #central
}

class EdiTalker ():
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

    def _getPartner(picking, atype, partner_id):
        line = '{:<6}'.format('SEH1D')
        line = line + '{:<3}'.format(atype)
        if partner_id in EDI_PARTNER:
            gln = EDI_PARTNER[partner_id]
        else:
            try:
                _partner = EdiTalker.getGLNFromPartnerId(partner_id)
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
        #saleOrder = self.loadSaleOrder(int(original_order['odoo_order_id']))
        
        picking = EdiTalker.getPickingFromOrder( env, order )

        orderNumber = order["x_edi_order"]
        #fileName = os.path.join(path, str(picking['id'])+'.txt')
        data = EdiTalker.getGLNFromPartnerId(env, order['partner_invoice_id']['id'])

        #file = open(fileName,"w") 

        line = ""
        line += EdiTalker.writeEncoded(EdiTalker._getHeader( order["x_edi_shipment"], 'DESADV', data["ref"]) )
        line += EdiTalker.writeEncoded(EdiTalker._getGlobalData(picking, order["x_edi_shipment"], orderNumber)  )
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(picking, 'MS', 'B86133188')  ) # Emisor
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(picking, 'SU', 'B86133188')  ) # Receptor del mensaje
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(picking, 'MR', order['partner_invoice_id']['id'])  ) # Receptor del mensaje
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(picking, 'IV', order['partner_invoice_id']['id'])  ) # Receptor del mensaje 
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(picking, 'DP', order['partner_shipping_id']['id'])  ) # Almacén 5663 por ejemplo
        line += EdiTalker.writeEncoded(EdiTalker._getPartner(picking, 'BY', order["partner_id"]['id'])  ) # Tienda compradora (destino final - viene del EDI del pedido)

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



class WrongFileException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)