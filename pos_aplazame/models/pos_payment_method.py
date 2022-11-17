from odoo import _, fields, models, api
import hmac, base64, struct, hashlib, time, os
import requests
import logging
import json
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"
    _description = 'Aplazame payment method'

    def _get_payment_terminal_selection(self):
        res = super()._get_payment_terminal_selection()
        res.append(("aplazame_payment", _("Aplazame")))
        return res

    def _call(self, key, url, data = False):
        mode = ""        
        if self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_sandbox_mode'):
            mode = ".sandbox"
        hed = {
            'Authorization': f"Bearer {key}",
            'Accept': f"application/vnd.aplazame{mode}.v3+json"
        }
        try:
            if data:
                response = requests.post(url, headers=hed, json=data)
            else:
                response = requests.get(url, headers=hed)

            return response
        except Exception as e:
            _logger.error(f"Zacalog: api call exception: "+str(e))
            return False

    def _getStatus(self, key, checkoutId):
        url = f"https://api.aplazame.com/checkout/{checkoutId}/status"
        return self._call(key, url)

    def _getOrder(self, key, orderId):
        url = f"https://api.aplazame.com/orders/{orderId}"
        return self._call(key, url)

    def _create(self, key, orderId, data):
        articles = []
        for article in data['articles']:
            product_obj = self.env['product.product']
            cursor = product_obj.search_read([('id', '=', article['id'])], ['name'])
            for _product in cursor:
                articles.append({
                    "id": article['id'],
                    "name": _product['name'],
                    "quantity": article['qty'],
                    "price": article['price'] / article['qty'],
                    #"tax_rate": 2100,
                    "discount_rate": 0,
                    "description": _product['name']
                })

        customer = {
            "email": data['email']
        }
        if 'phone' in data:
            customer['phone'] = data['phone']
        dataParams = {  
            "merchant": {
                "ipn_url": "https://mozo.zacatrus.es"
            },
            "order": {
                "id": orderId,
                "total_amount": data['amount']*100,
                "articles": articles,
                "currency": "EUR"
            },
            "customer": customer
        }
        url = f"https://api.aplazame.com/checkout/offline"
        return self._call(key, url, dataParams)

    @api.model
    def aplazame(self, posId, name, _data):
        config_obj = self.env['pos.config']
        cursor = config_obj.search([('id', '=', posId)])
        data = json.loads(_data)
        apiKey = None
        shopCode = "Z"
        for _client in cursor:
            apiKey = _client.x_aplazame_key
            shopCode = _client.x_shop_code

        if apiKey:
            orderId = shopCode + "_" + name.replace(" ", "-")
            response = self._getOrder(apiKey, orderId)
            if response != False:
                code = response.status_code
                info = response.json()
                if code >= 200 and code < 300:
                    if info["status"] == "pending":
                        return {"ok": False, "cause": "La solicitud aún se está procesando."}
                    elif info['status'] == 'ko':
                        cause = f"La solicitud ha fallado con este motivo '{info['status_reason']}'"
                        if info['status_reason'] == 'expired':
                            cause = "La solicitud ha expirado. Por favor, cancela el pedido y empieza de nuevo."
                        return {"ok": False, "cause": cause}
                    elif info['status'] == 'ok':
                        if data['amount']*100 == info["total_amount"]:
                            return {"ok": True, "cause": ""}
                        else:
                            return {"ok": False, "cause": f"La cantidad a cobrar tiene que ser exactamente la misma que la de la primera solicitud: "+str(info["total_amount"]/100)}
                    else:
                        return {"ok": False, "cause": f"La solicitud está en estado {info['status']}."}
                elif code == 404:
                    response = self._create(apiKey, orderId, data)
                    if response != False:
                        code = response.status_code
                        info = response.json()
                        if code >= 200 and code < 300:
                            return {"ok": False, "cause": "Solicitud envíada. Esperamos respuesta."}
                        else:
                            _logger.error(f"Zacalog: Aplazame error "+ json.dumps(info))
                return {"ok": False, "cause": f"code: {code}."}
            else:
                _logger.error(f"Zacalog: No response from Aplazame")
        else:
            _logger.error(f"Zacalog: Aplazame private api key not set.")

        return {"ok": False, "cause": "Ops, algo ha ido mal :-/"}