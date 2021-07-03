from odoo import _, fields, models, api
import hmac, base64, struct, hashlib, time, os
import requests
import logging
_logger = logging.getLogger(__name__)   

def normalize(key):
    """Normalizes secret by removing spaces and padding with = to a multiple of 8"""
    k2 = key.strip().replace(' ','')
    # k2 = k2.upper()   # skipped b/c b32decode has a foldcase argument
    if len(k2)%8 != 0:
        k2 += '='*(8-len(k2)%8)
    return k2

def get_hotp_token(secret, intervals_no):
    """This is where the magic happens."""
    key = base64.b32decode(normalize(secret), True) # True is to fold lower into uppercase
    msg = struct.pack(">Q", intervals_no)
    h = bytearray(hmac.new(key, msg, hashlib.sha1).digest())
    o = h[19] & 15
    h = str((struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000)
    return prefix0(h)

def get_totp_token():
    secret = 'KPX24GQ2O553RI3OIBHEVIKQUYNH4YJ523WNFYL72AHNLUBNL5X7JJQDUXIOYIDBN3PHKAWZAFYNM6QNIPOION6BZHCK3Q3EWUCESKBS22WN5NLLDY2YCRUGTPZ56Q3WJUUQLPUNY2VEZQSU6ASOZDAF4EMBOBCUWZEXHXGCUEW3I5ZXV2WHY46GJAOFBZU7XD2C756M2KBHM'

    """The TOTP token is just a HOTP token seeded with every 30 seconds."""
    return get_hotp_token(secret, intervals_no=int(time.time())//30)

def prefix0(h):
    """Prefixes code with leading zeros if missing."""
    if len(h) < 6:
        h = '0'*(6-len(h)) + h
    return h

class GiftCard():
    def __init__(self, url, username, password):
        self.username = username
        self.password = password
        self.url = url

    def _getToken(self):
        data = {"username": self.username, "password": self.password, "otp": get_totp_token()}
        #print(data)

        if "dummy" in self.url:
          url = self.url + "integration/admin/token"
        else:
          url = self.url + "tfa/provider/google/authenticate"

        try:
            response = requests.post(url, json=data)
            self.gtoken = response.json()
            if response.status_code == 200:
                return self.gtoken
        except Exception as e:
            print ("Cannot access.\n")
            
        return False

    def _getData(self, url, postParams=False, method = False):
        token = self._getToken()
        if token:
            hed = {'Authorization': 'Bearer ' + token}
            if method and method == 'put':
                response = requests.put(self.url + url, headers=hed, json=postParams)
            elif postParams:
                response = requests.post(self.url + url, headers=hed, json=postParams)
            else:
                response = requests.get(self.url + url, headers=hed)

            return response.json()
        else:
            return False

    def getGiftCardByCode(self, code):
        return self._getData("mpgiftcard/code/?searchCriteria[filterGroups][0][filters][0][field]=code&searchCriteria[filterGroups][0][filters][0][value]="+code)

    def updateGiftCard(self, data):
        _data = {"entity": data}
        return self._getData("mpgiftcard/code/", _data, "put")

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"
    _description = 'Tarjezaca payment method'

    def _get_payment_terminal_selection(self):
        res = super()._get_payment_terminal_selection()
        res.append(("tarjezaca_payment", _("Tarjezaca")))
        return res

    @api.model
    def redeem(self, code, amount):
        magento_url = self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.magento_url')
        magento_user = self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.magento_user')
        magento_password = self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.magento_password')

        magento_client = GiftCard(
            magento_url, 
            magento_user, 
            magento_password
        )
        mCards = magento_client.getGiftCardByCode(code)
        ok = False
        cause = None
        if not mCards:
            cause = "No puedo conectar con Magento"
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
                        if not magento_client.updateGiftCard(data):
                            cause = "Error al hacer la transacción"
                        else:
                            #cause = "Redeem "+str(amount)+" out of "+str(mCard["balance"])
                            ok = True     

        return {"ok": ok, "cause": cause}

