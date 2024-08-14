import re
import json
import requests
import string
import random
import sys
import logging
import hmac, base64, struct, hashlib, time, os

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

def get_totp_token( secret ):
    """The TOTP token is just a HOTP token seeded with every 30 seconds."""
    return get_hotp_token(secret, intervals_no=int(time.time())//30)

def prefix0(h):
    """Prefixes code with leading zeros if missing."""
    if len(h) < 6:
        h = '0'*(6-len(h)) + h
    return h

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

from odoo import models, fields, api
class Zconnector(models.Model):
    _name = 'zacatrus.connector'
    _description = 'Zacatrus Connector'

    CONFIG_DATA = {}

    def _getConfigData(self):
        self.CONFIG_DATA['apiUrl'] = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_url')
        if not self.CONFIG_DATA['apiUrl']:
            raise Exception("Connection not configured.")
        self.CONFIG_DATA['apiUrl'] = self.CONFIG_DATA['apiUrl'].replace("/rest/all/V1/", "")
        self.CONFIG_DATA['apiUrl'] = self.CONFIG_DATA['apiUrl'].replace("/rest/all/V1", "")
        self.CONFIG_DATA['apiUrl'] = self.CONFIG_DATA['apiUrl'].replace("/rest/V1/", "")
        self.CONFIG_DATA['apiUrl'] = self.CONFIG_DATA['apiUrl'].replace("/rest/V1", "")

        self.CONFIG_DATA['apiuser'] = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_user')
        self.CONFIG_DATA['apipass'] = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_password')
        self.CONFIG_DATA['apisecret'] = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_secret')

    def _getUrl(self, isCustomer = False):
        if isCustomer:
          return self.CONFIG_DATA['apiUrl'] + "/rest/V1/"
        else:
          return self.CONFIG_DATA['apiUrl'] + "/rest/all/V1/"

    def _getToken(self, user = None, password = None):
        self._getConfigData()

        token = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_token')
        if token:
            return token

        data = {
            "username": self.CONFIG_DATA['apiuser'] if not user else user, 
            "password": self.CONFIG_DATA['apipass'] if not password else password, 
            "otp": get_totp_token(self.CONFIG_DATA['apisecret'])
        }
        _logger.warning("T_ZB: username: "+ str(user))

        if user:
          url = self._getUrl(True) + "integration/customer/token"
        else:
            if "dummy" in self._getUrl():
                url = self._getUrl() + "integration/admin/token"
            else:
                url = self._getUrl() + "tfa/provider/google/authenticate"

        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                gtoken = response.json()
                return gtoken
        except Exception as e:
            _logger.warning("P_ZB: e: " + str(e))
            print ("Cannot access.\n")
            
        _logger.error("P_ZB: auth failed. Cannot get token.")
        return False

    def _getData(self, purl, postParams=False, method = False, token = None):
        isCustomer = False
        if not token:
            token = self._getToken()
        else:
            isCustomer = True

        if token:
            hed = {'Authorization': 'Bearer ' + token}
            if method and method == 'put':
                response = requests.put(self._getUrl(isCustomer) + purl, headers=hed, json=postParams)
            elif postParams:
                response = requests.post(self._getUrl(isCustomer) + purl, headers=hed, json=postParams)
            else:
                response = requests.get(self._getUrl(isCustomer) + purl, headers=hed)

            return response.json()
        else:
            _logger.error("P_ZB: _getData failed for purl: " + purl)
            return False

    def getCustomerByEmail(self, email):
        return self._getCustomerByEmail(email)
    
    def _getCustomerByEmail(self, email):
        sCriteria = "searchCriteria[filterGroups][0][filters][0][field]=email"
        sCriteria += "&" + "searchCriteria[filterGroups][0][filters][0][value]="+email

        customers = self._getData('customers/search?'+ sCriteria)
        if customers:
            for customer in customers["items"]:
                return customer

        return None
    
    def getRule(self, ruleId = 8):
        return self._getData('rewards/management/rule?rule_id=' + str(ruleId))

    def doAdd(self, customerId, qty, comment="Añadidos por el administrador", expire=365, action="admin"):
        #https://amasty.com/knowledge-base/what-amasty-magento-2-plugins-support-api.html#reward
        data = {
            "customer_id": customerId, 
            "amount": qty,
            "comment": comment,
            "action": action,
            "expire": {"expire": True, "days": expire}
        }
        res = self._getData('rewards/management/points/add', data)
        
        return not res

    def doDeduct(self, customerId, qty, comment="Eliminados por el administrador", action="admin"):
        data = {
            "customer_id": customerId, 
            "amount": qty,
            "comment": comment,
            "action": action
        }
        res = self._getData('rewards/management/points/deduct', data)

        return not res

    def doDeductBlocks(self, customerId, qty, comment="Eliminados por el administrador", action="admin"):
        done = False
        #print(order['discount_description'])
        left = fichasSpent = qty    
        expirations = self.getFichasExpiration( customerId )
        for expiration in expirations:
            #print(expiration['amount'])
            if expiration['amount'] < left:
                deductAmount = expiration['amount']
            else:
                deductAmount = left

            left -= deductAmount
            self.doDeduct(customerId, deductAmount) 
            if left <= 0:
                break
        if left > 0:
            deductAmount = left
            left -= deductAmount
            self.doDeduct(customerId, deductAmount)
        done = True
        
        return done

    def getFichasExpiration(self, customerId):
        res = self._getData('rewards/mine/expiration?customer_id=' + str(customerId))
        
        return res

    def getFichasHistory(self, customerId):
        res = self._getData('rewards/mine/history?customer_id=' + str(customerId))
        
        return res

    def _getPoints(self, customerId):
        res = self._getData('rewards/mine/balance?customer_id='+ str(customerId))

        return res

    def _getFichas(self, token):
        res = self._getData( 'rewards/mine/balance', False, False, token )
        return res

    @api.model
    def getToken(self, user, password):
        return self._getToken(user, password)

    @api.model
    def getUserData(self, token):
        return {
            "fichas": self._getFichas(token)
        }

    def getBalance( self, email ):
        fichas = 0
        _logger.info("T_ZB: getBalance: email: "+ email)
        mCustomer = self._getCustomerByEmail(email)
        if mCustomer:
            _logger.info("T_ZB: getBalance: mCustomer id: "+ str(mCustomer["id"]))
            fichas = self._getPoints( mCustomer["id"] )
            _logger.info("T_ZB: getBalance: fichas: "+ str(fichas))

        return fichas
        
    def getGiftCardByCode(self, code):
        return self._getData("mpgiftcard/code/?searchCriteria[filterGroups][0][filters][0][field]=code&searchCriteria[filterGroups][0][filters][0][value]="+code)

    def updateGiftCard(self, data):
        _data = {"entity": data}
        return self._getData("mpgiftcard/code/", _data, "put")

    def createCustomer(self, email, name, posName = False):
        groupId = 1

        if posName:
            _m = re.search('adrid', posName)
        if _m:
            groupId = 18
        _m = re.search('evilla', posName)
        if _m:
            groupId = 19
        _m = re.search('alencia', posName)
        if _m:
            groupId = 20
        _m = re.search('arcelona', posName)
        if _m:
            groupId = 21
        _m = re.search('itoria', posName)
        if _m:
            groupId = 22
        _m = re.search('mides', posName)
        if _m:
            groupId = 23
        _m = re.search('aragoza', posName)
        if _m:
            groupId = 24
        _m = re.search('alladolid', posName)
        if _m:
            groupId = 25

        customer = {
            'customer': {
                'email': email,
                'firstname': name,
                'lastname': '.',
                #'password': id_generator(),
                'website_id': '1',
                'group_id': groupId
            }
            , 'password': 'Aa1'+id_generator(8)
        }
        res = self._getData('customers', customer)
        return res