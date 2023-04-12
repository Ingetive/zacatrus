import logging
from odoo import http
import datetime
import hmac, base64, struct, hashlib, time, os
import json
_logger = logging.getLogger(__name__)

class PaylandsController(http.Controller):
    @http.route('/payment/paylands/return', auth='public', type="json")
    def handler(self):
        notification = http.request.jsonrequest

        _logger.debug("Zacalog: Paylands callback: "+ str(notification))

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
                args = [
                    ('order_id', '=', notification['order']['reference'])
                ]
                payments = http.request.env["pos_paylands.payment"].search(args)
                for payment in payments:
                    if ( (payment['amount'] < 0 and notification['order']['status'] == 'SUCCESS') or 
                        (payment['amount'] > 0 and notification['order']['status'] in ['SUCCESS', 'REFUNDED', 'PARTIALLY_REFUNDED']) ):
                        ok = False
                        status = 502
                    else:
                        data = None
                        if notification['order']['status'] == 'SUCCESS' and notification['order']['amount'] != payment['amount']:
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
        ticketFooter = f"------------------------------------------<br />"
        ticketFooter += f"DATOS TARJETA:<br />"
        ticketFooter += f"Id. transacción: {notification['order']['uuid']}<br />"
        ticketFooter += f"Fecha: {when.strftime('%d/%m/%Y')}<br />"
        ticketFooter += f"Hora: {when.strftime('%H:%M:%S')}<br />"
        ticketFooter += f"Cantidad: {amount}<br />"
        ticketFooter += f"Cod. moneda: {notification['order']['currency']}<br />"
        ticketFooter += f"Servicio: {notification['order']['service']}<br />"
        ticketFooter += f"Tipo: {transaction['pos']['brand']}<br />"
        ticketFooter += f"Tarjeta: {transaction['pos']['masked_pan']}<br />"
        ticketFooter += f"Met. verificación: {transaction['pos']['verification_method']}<br />"
        ticketFooter += f"Mod. entrada: {transaction['pos']['entry_mode']}<br />"
        ticketFooter += f"------------------------------------------<br />"

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