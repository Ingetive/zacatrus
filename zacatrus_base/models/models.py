import datetime
import requests
import string
import random
import logging
import hmac, base64, struct, hashlib, time
from odoo import models, api

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

class Zconnector(models.Model):
    _name = 'zacatrus.connector'
    _description = 'Zacatrus Connector'

    CONFIG_DATA = {}

    def _getConfigData(self):
        #self.CONFIG_DATA['apiUrl'] = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_url')
        self.CONFIG_DATA['apiUrl'] = self.env['res.config.settings'].getMagentoUrl()
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
        #_logger.error(f"Zacalog: doDeduct {res}")

        return not res

    def doDeductBlocks(self, customerId, qty, comment="Eliminados por el administrador", action="admin"):
        done = False
        #print(order['discount_description'])
        left = qty    
        expirations = self.getFichasExpiration( customerId )
        for expiration in expirations:
            #print(expiration['amount'])
            if expiration['expiring_amount'] < left:
                deductAmount = expiration['expiring_amount']
            else:
                deductAmount = left

            ok = self.doDeduct(customerId, deductAmount, comment) 
            if ok:
                left -= deductAmount
            else:
                break
            if left <= 0:
                break
        if left > 0:
            deductAmount = left
            ok = self.doDeduct(customerId, deductAmount, comment)
            if ok:
                left -= deductAmount
        if left <= 0:
            done = True
        
        return left

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
        mCustomer = self._getCustomerByEmail(email)
        if mCustomer:
            fichas = self._getPoints( mCustomer["id"] )

        return fichas
        
    def getGiftCardByCode(self, code):
        return self._getData("mpgiftcard/code/?searchCriteria[filterGroups][0][filters][0][field]=code&searchCriteria[filterGroups][0][filters][0][value]="+code)

    def updateGiftCard(self, data):
        _data = {"entity": data}
        return self._getData("mpgiftcard/code/", _data, "put")

    def createGiftCard(self, data):
        _data = {"entity": data}
        return self._getData("mpgiftcard/code/", _data, "put")

    def createCustomer(self, email, name, posName = False):
        groupId = 1

    def _getStock(self, sku, source = None, multi = False):
        if not source:
            source = "WH"

        if not sku or sku == "":
            return False
        
        url_ = "inventory/source-items"
        query = "searchCriteria[filter_groups][0][filters][0][field]=sku&searchCriteria[filter_groups][0][filters][0][value]="+sku+"&searchCriteria[filter_groups][0][filters][0][condition_type]=eq"
        url = url_+"?"+query

        response = self._getData(url)

        ret = False
        if not response or "message" in response:
            _logger.error(f"Zacalog: Error getting stock for {sku}: {response['message']}")
        else:
            for item in response["items"]:
                if item["source_code"] == source:
                    item["qty"] = item["quantity"]
                    ret = item
                if not ret:
                    response["qty"] = 0
                    ret = response

        return ret
        
    def increaseStock(self, sku, qty, setLastRepo = False, source = False):
        self.decreaseStock(sku, qty*(-1), setLastRepo, source)

    def decreaseStock(self, sku, qty, setLastRepo = False, source = False):
        self._queueStockUpdate(sku, qty, True, setLastRepo, source)
        
    def _queueStockUpdate(self, sku, qty, relative = True, setLastRepo = False, source = "WH"):
        if relative and qty == 0:
            return
    
        if isinstance(source, int):
            sourceCode = self.sourceCodes[source]
        else:
            sourceCode = source

        lastRepo = False
        if setLastRepo:
            lastRepo = str(datetime.datetime.now())

        #db =  self._getMongoDb()
        #db.queue.bulk_write([InsertOne({'sku': sku, 'qty': qty, 'relative': relative, 'last_repo': lastRepo, 'created_at': datetime.now(), 'source': sourceCode})])
        #db.stocklog.bulk_write([InsertOne({'sku': sku, 'qty': qty, 'relative': relative, 'last_repo': lastRepo, 'created_at': datetime.now(), 'source': sourceCode})])

        data = {'sku': sku, 'qty': qty, 'relative': relative, 'last_repo': lastRepo, 'create_date': datetime.datetime.now(), 'source': sourceCode, 'done': False}

        self.env['zacatrus_base.queue'].create( data )

    def _doDecreaseStock(self, sku, qty, source = False):
        try:
            curStock = self._getStock( sku, source )
            if not curStock:
                return False

            if 'qty' in curStock:
                if curStock['qty'] == None:
                    curStock['qty'] = 0
                return self._doPutStock(sku, curStock['qty']-qty, source)
        except Exception as e:
            _logger.error(f"Zacalog: _doDecreaseStock exception: "+ str(e))            
            return False

        _logger.error(f"Zacalog: _doDecreaseStock: No quantities got from magento for {sku}")
        return False


    def _doPutStock(self, sku, qty, source = False, manageStock = True):
        ret = False
        method = False
        if source:
            postParams = {"sourceItems": [{"sku": sku,"source_code": source, "quantity": qty,"status": 1 if qty > 0 else 0,"extension_attributes": { } }]}
            url = "inventory/source-items"
        else:
            postParams = {"stockItem":{"qty":qty, "is_in_stock": (qty > 0), "manage_stock": manageStock}}
            url = "products/"+sku+"/stockItems/1"
            method = "put"

        try:
            self._getData(url, postParams, method)
        except Exception as e:
            _logger.error(f"Zacalog: _doPutStock exception: "+ str(e))
            return False
            
        return True


    def _procItem(self, item):
        ok = False

        #source = False
        if 'source' in item:
            source = item['source']
        else:
            source = self.defaultStockSource
        if item['sku']:
            if not item["relative"]:
                #TODO: De momento son todos relativos
                pass #ok = self._doPutStock(item["sku"], item["qty"], source)
            else:
                ok = self._doDecreaseStock(item["sku"], item["qty"], source)
        else:
            ok = True

        if ok and item.sku and item.last_repo:
            self.setProductAttribute(item.sku, "last_repo", item.last_repo)

        if ok:
            item.write({"done": True})
        else:
            _logger.error("Zacalog: Syncer: Error updating " + item["sku"])

            #if (datetime.now() - item["created_at"]) > timedelta(minutes=60):
            #    self._getSlack().sendRedAlertLimited(f"Error updating stock of product with sku {item['sku']} for more than 60 minutes.")
            #
            #m = re.search("(.*)-1$", item["sku"])
            #if m:
            #    item["sku"] = m.group(1)
            #    self._procItem(item)

    def procStockUpdateQueue(self):
        items = self.env['zacatrus_base.queue'].search([('done', '=', False)])
        for item in items:
            try:
                self._procItem(item)
            except Exception as e:
                _logger.error(f"Zacalog: Error syncing item {item['sku']}: {e}")