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
        return f"https://api.paylands.com/v1{sandboxText}/posms/payment"

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

        orderNumber = name.replace(" ", "-")
        orderId = f"POS{posId}_{orderNumber}"
        code = 0
        message = ''
        status = 0
        ok = False

        payments = self.env["pos_paylands.payment"].search_read(domain=[("order_id", "=", orderId)])
        dbPayment = False
        for payment in payments:
            dbPayment = payment
            status = payment['status']
            message = 'Creado'
            ok = True

        if not dbPayment:
            notificationUrl = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_notification_url')
            hed = {'Authorization': 'Bearer ' + apiKey}
            postParams = {
                "signature": signature,
                "device": posParams['device'],
                "amount": data['amount']*100,
                "description": f"{name}",
                "url_post": notificationUrl,
                "reference": orderId,
                "customer_ext_id": "12345678Z",
                "additional": "Additional info"
            }
            response = requests.post(url, headers=hed, json=postParams)
            if response.status_code == 200:  
                ok = True
                self.env["pos_paylands.payment"].create({
                    "order_id": orderId,
                    "status": status,
                    "amount": data['amount']
                })
            res = response.json()
            message = res['message']
            code = res['code']

        return {"ok": ok, 'code': code, 'message': message, 'status': status}

    @api.model
    def get_status(self, methodId, saleId):
        return 1

    @api.model
    def cancel(self, methodId, saleId):
        return 1