import datetime, logging
from odoo import models, fields, api

DISTRI_WAREHOUSE_ID = 21
DISTRI_TEAM_ID = 2
EDI_USER_ID = 127


_logger = logging.getLogger(__name__)

class EdiWriter ():
    EDI_STATUS_INIT = 1

    def createOrRetrieveECIClient(env, aPartner):
        args = [('ref', '=', aPartner["code"])] #query clause
        #ids = self.sock.execute(self.dbname, self.uid, self.pwd, 'res.partner', 'search', args)
        partners = env['res.partner'].search(args)
        if len(partners) == 0:
            raise Exception("No tenemos cliente creado para este código: "+ aPartner["code"]) # we don't create it anymore
        else:
            partner = partners[0]

        return partner['id']
    
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
    
    def createSaleOrderFromEdi(env, ediOrder, filename):
        #userId = 127

        invoicingPartner = ""
        shippingPartner = False
        buyerPartner = False
        try:
            for partner in ediOrder['partner']:
                if partner ['calificator'] == "IV":
                    invoicingPartner = EdiWriter.createOrRetrieveECIClient( env, partner )
                if partner ['calificator'] == "DP":
                    shippingPartner = EdiWriter.createOrRetrieveECIClient( env, partner )
                if partner ['calificator'] == "BY":
                    buyerPartner = EdiWriter.createOrRetrieveECIClient( env, partner )
                #print (partner)
        except Exception as e:
            EdiWriter.saveError(env, 101, ediOrder, str(e))
            raise e


        if invoicingPartner not in [5661, 5967, 5758]: # ECI, Juguettos, Fnac
            EdiWriter.saveError(env, 102, ediOrder, "No es ninguno de los clientes de EDI.")
            raise Exception(f"wrong client {invoicingPartner}")

        if not shippingPartner:
            EdiWriter.saveError(env, 103, ediOrder, "Dirección de envío incorrecta.")
            raise Exception("wrong shipping address")
      
        args = [('client_order_ref', '=', ediOrder['data']['orderNumber'])]
        dups = env['sale.order'].search(args)
        if len(dups) > 0:
            EdiWriter.saveError(env, 104, ediOrder, "Este pedido ya está creado.")
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
            'x_edi_status': EdiWriter.EDI_STATUS_INIT
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
                EdiWriter.saveError(env, 105, ediOrder, "El producto con código de barras {item['barcode']} no existe.")
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

                _logger.info(order_line)
                lineId =  env['sale.order.line'].create(order_line)

        return createdOrder