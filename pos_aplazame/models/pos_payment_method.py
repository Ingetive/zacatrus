from odoo import _, fields, models, api
import hmac, base64, struct, hashlib, time, os
import requests
import logging
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"
    _description = 'Aplazame payment method'

    def _get_payment_terminal_selection(self):
        res = super()._get_payment_terminal_selection()
        res.append(("aplazame_payment", _("Aplazame")))
        return res

    def _call(self, key, url, data = False):
        hed = {
            'Authorization': f"Bearer {key}",
            'Accept': 'application/vnd.aplazame.v3+json'
        }
        try:
            if data:
                response = requests.post(url, json=data)
            else:
                response = requests.get(url)

            return response
        except Exception as e:
            _logger.error(f"Zacalog: api call exception: "+str(e))
            return False

    def _getStatus(self, key, checkoutId):
        url = f"https://api.aplazame.com/checkout/{checkoutId}/status"
        return self._call(key, url)

    def _create(self, key, data):
        pass # TODO

    @api.model
    def aplazame(self, posId, name):
        config_obj = self.env['pos.config']
        cursor = config_obj.search([('id', '=', posId)])
        apiKey = None
        for _client in cursor:
            _logger.warning(f"Zacalog: {_client.x_aplazame_key}")
            apiKey = _client.x_aplazame_key

        if apiKey:
            checkoutId = name.replace(" ", "-")
            response = self._getStatus(apiKey, checkoutId)
            if response != False:
                code = response.status_code
                _logger.warning(f"Zacalog: Response code {code}")
                if code >= 200 and code < 300:
                    info = response.json()
                elif code == 404:
                    _logger.warning(f"Zacalog: code: {code}")
                    return {"ok": False, "cause": "Pedido no encontrado. Aquí deberíamos estar creandolo."}
                return {"ok": False, "cause": f"code: {code}."}
            else:
                _logger.error(f"Zacalog: No response from Aplazame")
        else:
            _logger.error(f"Zacalog: Aplazame private api key not set.")

        return {"ok": False, "cause": f"Zacalog: {posId} {checkoutId}"}