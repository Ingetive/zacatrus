from odoo import _, fields, models, api
import hmac, base64, struct, hashlib, time, os
import requests
import logging
import json
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"
    _description = 'Paylands payment method'

    def _getBaseUrl(self, sandbox = False):
        sandboxText = "/sandbox" if sandbox else ""
        return f"https://api.paylands.com/v1{sandboxText}"

    def _get_payment_terminal_selection(self):
        res = super()._get_payment_terminal_selection()
        res.append(("paylands_payment", _("Paylands")))
        return res

    def _getPosParams(self, posId):
        config_obj = self.env['pos.config']
        cursor = config_obj.search([('id', '=', posId)])
        ret = {'device': None}
        for _client in cursor:
            ret['device'] = _client.x_paylands_device

        return ret

    @api.model
    def paylands(self, posId, name, _data):
        url = self._getBaseUrl(
            self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_sandbox_mode')
        )
        apiKey = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_apikey')
        signature = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_signature')
        posParams = self._getPosParams(posId)
        data = json.loads(_data)

        orderNumber = name
        part = name.split(" ")
        if len(part) == 2:
            orderNumber = part[1]
        orderId = f"{orderNumber}"
        code = 0
        message = ''
        status = 0
        ok = False

        payments = self.env["pos_paylands.payment"].search([("order_id", "=", orderId)])
        dbPayment = False
        for payment in payments:
            dbPayment = payment
            status = payment['status']
            message = 'Creado'
            ok = True

        if status not in [200]:
            if data['amount'] < 0:
                orderCode = data['order'].replace(" ", "")
                prevOrderId = f"{orderCode}"
                _logger.warning(f"Zacalog: paylands prevOrderId: {prevOrderId}")
                payments = self.env["pos_paylands.payment"].search([("order_id", "=", prevOrderId)])
                found = False
                for payment in payments:
                    found = True
                    code = 500
                    hed = {'Authorization': 'Bearer ' + apiKey}
                    postParams = {
                        "signature": signature,
                        "device": posParams['device'],
                        "order_uuid": payment['uuid'],
                        "amount": int(round(data['amount']*100)*-1)
                    }
                    response = requests.post(f"{url}/posms/refund", headers=hed, json=postParams)

                    res = response.json()
                    message = res['message']
                    if response.status_code == 200:
                        ok = True
                        if not dbPayment:
                            self.env["pos_paylands.payment"].create({
                                "order_id": orderId,
                                "status": status,
                                "refund_order_id": prevOrderId,
                                "amount": int(round(data['amount']*100))
                            })
                        else:
                            dbPayment.write({
                                'status' : 0,
                                "amount": int(data['amount']*100)
                            })
                        #payment.write( {'return_order_id': orderId} )
                    else:
                        code = response.status_code
                        message = res['message']

                if not found:
                    code = 404
                    message = "No encuentro el pedido original. ¿Lo has tecleado bien?"
            elif data['amount'] > 0:
                #notificationUrl = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_notification_url')
                baseUrl = self.env['ir.config_parameter'].get_param('web.base.url')
                notificationUrl = f"{baseUrl}/payment/paylands/return"
                hed = {'Authorization': 'Bearer ' + apiKey}
                postParams = {
                    "signature": signature,
                    "device": posParams['device'],
                    "amount": int(round(data['amount']*100)),
                    "description": f"{name}",
                    "url_post": notificationUrl,
                    "reference": orderId,
                    "customer_ext_id": str(data['client']),
                    "additional": orderId
                }
                _logger.warning(f"Zacalog: paylands {postParams}")
                response = requests.post(f"{url}/posms/payment", headers=hed, json=postParams)

                res = response.json()
                _logger.warning(f"Zacalog: paylands res: {res}")
                message = ''
                if 'message' in res:
                    message = res['message']
                if 'details' in res:
                    message += res['details']
                code = res['code']
                if response.status_code == 200:  
                    ok = True
                    if not dbPayment:
                        self.env["pos_paylands.payment"].create({
                            "order_id": orderId,
                            "status": status,
                            "amount": int(round(data['amount']*100))
                        })
                    else:
                        dbPayment.write({
                            'status' : 0,
                            "amount": int(data['amount']*100)
                        })
                else:
                    status = response.status_code
            else:
                ok = True

        return {"ok": ok, 'code': code, 'message': message, 'status': status}

    @api.model
    def get_status(self, posId, name):
        ret = 0
        orderNumber = name        
        part = name.split(" ")
        if len(part) == 2:
            orderNumber = part[1]
        orderId = f"{orderNumber}"

        payments = self.env["pos_paylands.payment"].search_read(domain=[("order_id", "=", orderId)])
        ret = {'status': 0, 'additional' : {}}
        for payment in payments:
            ret = {'status': payment['status'], 'additional' : {}}
            if payment['status'] == 200:
                ret['additional'] = {      
                    'uuid': payment['uuid'],
                    'masked_pan': payment['masked_pan'],
                    'brand': payment['brand'],
                    'ticket_footer': payment['ticket_footer']
                }
            elif payment['status'] == 202:
                pass

        return ret

    @api.model
    def cancel(self, posId, name):
        ret = 0

        orderNumber = name
        part = name.split(" ")
        if len(part) == 2:
            orderNumber = part[1]
        orderId = f"{orderNumber}"

        args = [
            ('order_id', '=', orderId)
        ]
        payments = self.env["pos_paylands.payment"].search(args)
        for payment in payments:
            res = payment.write({'status': 300})
            if res:
                ret = 300

        return ret
