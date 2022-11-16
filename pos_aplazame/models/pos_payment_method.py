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

    @api.model
    def aplazame(self, code, amount):
        return {"ok": True, "cause": ""}