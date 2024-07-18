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



class WrongFileException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)