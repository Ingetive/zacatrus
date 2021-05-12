import re
import json
import requests
import string
import random
import sys
import logging
import hmac, base64, struct, hashlib, time, os

_logger = logging.getLogger(__name__)

url = 'https://zacatrus.es/rest/all/V1/'
apiuser = 'zaca24'
apipass = 'carracacosa1'
FICHAS_BARCODE = "100001"

def normalize(key):
	"""Normalizes secret by removing spaces and padding with = to a multiple of 8"""
	k2 = key.strip().replace(' ','')
	# k2 = k2.upper()	# skipped b/c b32decode has a foldcase argument
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

class Fichas():
	def __init__(self, url, username, password):
		self.username = username
		self.password = password
		self.url = url

	def _getToken(self):
		data = {"username":self.username,"password": self.password, 'otp': get_totp_token()}

		response = requests.post(self.url + 'tfa/provider/google/authenticate', json=data, headers={})

		return response.json()

	def _getData(self, url, postParams=False):
		token = self._getToken()
		if token:
			hed = {'Authorization': 'Bearer ' + token}
			if postParams:
				response = requests.post(self.url + url, headers=hed, json=postParams)
			else:
				response = requests.get(self.url + url, headers=hed)
			return response.json()
		else:
			return False

	# New methods (Amasty reward extension)
	def getCustomerByEmail(self, email):
		sCriteria = "searchCriteria[filterGroups][0][filters][0][field]=email"
		sCriteria += "&" + "searchCriteria[filterGroups][0][filters][0][value]="+email

		customers = self._getData('customers/search?'+ sCriteria)
		if customers:
			for customer in customers["items"]:
				return customer

		return None

	def getPoints(self, customerId):
		res = self._getData('rewards/mine/balance?customer_id='+ str(customerId))

		return res
	# END: New methods (Amasty reward extension)

from odoo import models, fields, api
class Zacasocios(models.Model):
	_name = 'zacasocios.zacasocios'
	_description = 'Zacasocios'

	def _isEmployee(self, email):
		client_obj = self.env['res.partner']
		cursor = client_obj.search_read([('email', '=', email)], ['name', 'property_product_pricelist'])
		for _client in cursor:
			_m = re.search('mpleado', _client['property_product_pricelist'][1])
			if _m:
				return True

		return False

	def _clientAlreadySpent(self, email):
		client_obj = self.env['res.partner']
		pos_obj = self.env['pos.order']
		pos_item_obj = self.env['pos.order.line']
		product_obj = self.env['product.product']
		cursor = client_obj.search_read([('email', '=', email)])
		for _client in cursor:
		    args = [('state', '<>', "done" ),('partner_id', '=', _client["id"] )]
		    pos = pos_obj.search_read(args)
		    for po in pos:            
		        iargs = [("order_id", "=", po['id'])]
		        posOrdersItems = pos_item_obj.search_read(iargs)
		        for item in posOrdersItems:
		            pargs = [('id', '=', item['product_id'][0] )]
		            products = product_obj.search_read(pargs)
		            for product in products:
			            if(product['barcode'] == FICHAS_BARCODE):
			                if (item['qty'] and item['qty'] < 0):
			                    return True
		return False

	@api.model
	def getBalance( self, email, posName ):
		magento_client = Fichas(url, apiuser, apipass)

		fichas = 0
		if not self._isEmployee( email ) and not self._clientAlreadySpent(email):
			mCustomer = magento_client.getCustomerByEmail(email)
#			if mCustomer:
#				fichas = magento_client.getPoints( mCustomer["id"] )
#
#		return fichas
		return 15000
		

