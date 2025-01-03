import logging
from odoo import http
import datetime
import hmac, base64, struct, hashlib, time, os
import json
_logger = logging.getLogger(__name__)

class PaylandsController(http.Controller):
    @http.route('/payment/paylands/return', auth='public', type="json")
    def handler(self, **kwargs):
        notification = json.loads(http.request.httprequest.data)

        #_logger.info("Zacalog: Paylands callback: "+ str(notification))

        # Check hash
        signature = http.request.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_signature')
        array = {}
        array['order'] = notification['order']
        array['client'] = notification['client']
        #array['extra_data'] = None
        data = json.dumps(array, separators=(",", ":"))
        validationHash = hashlib.sha256((data + signature).encode())
        if validationHash.hexdigest() != notification['validation_hash']:
            raise Exception("Sorry, validation failed") 

        ok = False
        status = -1
        if notification['order']['status'] == 'REFUSED':
            args = [
                ('order_id', '=', notification['order']['reference'])
            ]
            payments = http.request.env["pos_paylands.payment"].search(args)
            for payment in payments:
                payment.write({'status': 506})
                status = 506
        elif notification['order']['status'] == 'CANCELLED':
            args = [
                ('order_id', '=', notification['order']['reference'])
            ]
            payments = http.request.env["pos_paylands.payment"].search(args)
            for payment in payments:
                payment.write({'status': 300})
                status = 300
        elif notification['order']['status'] == 'SUCCESS' or notification['order']['status'] in ['REFUNDED', 'PARTIALLY_REFUNDED']:
            lastTransaction = self._getLastTransaction(notification['order']['transactions'])

            if lastTransaction['status'] == 'SUCCESS':
                field = "order_id"
                if notification['order']['status'] in ['REFUNDED', 'PARTIALLY_REFUNDED']:
                    field = "refund_order_id"
                args = [
                    (field, '=', notification['order']['reference'])
                ]
                payments = http.request.env["pos_paylands.payment"].search(args)
                for payment in payments:
                    if not notification['order']['status'] in ['SUCCESS', 'REFUNDED', 'PARTIALLY_REFUNDED']:
                        _logger.error("Zacalog: Paylands callback failed.")
                        ok = False
                        status = 502
                    else:
                        data = None
                        if notification['order']['status'] == 'SUCCESS' and notification['order']['amount'] != payment['amount']:
                            _logger.error("Zacalog: Paylands callback failed 503.")
                            payment.write( {'status': 503} )
                        else:
                            payment.write( {
                                'uuid': notification['order']['uuid'],
                                #'cardType': notification['order']['reference'],
                                #'cardHolderName': notification['order']['reference'],
                                'masked_pan': lastTransaction['pos']['masked_pan'],
                                'brand': lastTransaction['pos']['brand'],
                                'status': 200,
                                'ticket_footer': self._getTicketFooter(notification, lastTransaction)
                            } )


        return {"ok": ok, "status": status}

    def _getTicketFooter(self, notification, transaction):
        when = datetime.datetime.strptime(notification['order']['created'], '%Y-%m-%dT%H:%M:%S%z')
        amount = notification['order']['amount']/100
        ticketFooter = f"------------------------------------------ \n"
        ticketFooter += f"DATOS TARJETA: \n"
        ticketFooter += f"Id. transacción: {notification['order']['uuid']} \n"
        ticketFooter += f"Fecha: {when.strftime('%d/%m/%Y')} \n"
        ticketFooter += f"Hora: {when.strftime('%H:%M:%S')} \n"
        ticketFooter += f"Cantidad: {amount} \n"
        ticketFooter += f"Cod. moneda: {notification['order']['currency']} \n"
        ticketFooter += f"Servicio: {notification['order']['service']} \n"
        ticketFooter += f"Tipo: {transaction['pos']['brand']} \n"
        ticketFooter += f"Tarjeta: {transaction['pos']['masked_pan']} \n"
        ticketFooter += f"Met. verificación: {transaction['pos']['verification_method']} \n"
        ticketFooter += f"Mod. entrada: {transaction['pos']['entry_mode']} \n"
        ticketFooter += f"------------------------------------------ \n"

        return ticketFooter


    def _getLastTransaction(self, transactions):
        lastTransaction = None
        lastTransactionDate = None
        for transaction in transactions:
            date = datetime.datetime.strptime(transaction['created'], "%Y-%m-%dT%H:%M:%S%z") #2023-04-11T17:07:24+0200
            if not lastTransaction or lastTransactionDate < date:
                lastTransaction = transaction
                lastTransactionDate = date

        return lastTransaction