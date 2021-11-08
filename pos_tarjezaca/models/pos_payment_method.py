from odoo import _, fields, models, api
import hmac, base64, struct, hashlib, time, os
import requests
import logging
_logger = logging.getLogger(__name__)   

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"
    _description = 'Tarjezaca payment method'

    def _get_payment_terminal_selection(self):
        res = super()._get_payment_terminal_selection()
        res.append(("tarjezaca_payment", _("Tarjezaca")))
        return res

    @api.model
    def redeem(self, code, amount):
        zacatrus = self.env['zacatrus.connector']
        mCards = zacatrus.getGiftCardByCode(code)
        ok = False
        cause = None
        if not mCards:
            cause = "No puedo conectar con Magento."
        else:
            if mCards['total_count'] == 0:
                cause = "Código no encontrado"
            else:
                for mCard in mCards["items"]:
                    if float(mCard["balance"]) < float(amount):
                        cause = "Saldo insuficiente."
                    else:                        
                        data = { 
                            "giftcard_id": mCard["giftcard_id"],
                            "balance": float(mCard["balance"]) - float(amount)
                        }
                        if not zacatrus.updateGiftCard(data):
                            cause = "Error al hacer la transacción"
                        else:
                            #cause = "Redeem "+str(amount)+" out of "+str(mCard["balance"])
                            ok = True     

        return {"ok": ok, "cause": cause}

