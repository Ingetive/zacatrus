#!/usr/bin/python

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

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

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
		print(data)

		response = requests.post(self.url + 'tfa/provider/google/authenticate', json=data, headers={})
		print (response)
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

	def _postData(self, url, data):
		hed = {'Authorization': 'Bearer ' + self._getToken()}

		#url = 'https://api.xy.com'
		response = requests.post(self.url + url, json=data, headers=hed)
		return response.json()



	# New methods (Amasty reward extension)
	def getCustomerByEmail(self, email):
		sCriteria = "searchCriteria[filterGroups][0][filters][0][field]=email"
		sCriteria += "&" + "searchCriteria[filterGroups][0][filters][0][value]="+email

		customers = self._getData('customers/search?'+ sCriteria)
		for customer in customers["items"]:
			return customer

		return None

	def getPoints(self, customerId):
		res = self._getData('rewards/mine/balance?customer_id='+ str(customerId))

		return res

	def add(self, customerId, qty, comment="Modificados por el administrador", expire=365, action="admin"):
		#https://amasty.com/knowledge-base/what-amasty-magento-2-plugins-support-api.html#reward
		data = {
			"customer_id": customerId, 
			"amount": qty,
			"comment": comment,
			"action": action,
			"expire": {"expire": True, "days": expire}
		}
		res = self._getData('rewards/management/points/add', data)
		
		return res

	def deduct(self, customerId, qty, comment="Eliminados por el administrador", action="admin"):
		data = {
			"customer_id": customerId, 
			"amount": qty,
			"comment": comment,
			"action": action
		}
		res = self._getData('rewards/management/points/deduct', data)
		
		return res
		
	def getRule(self, ruleId = 8):
		return self._getData('rewards/management/rule?rule_id=' + str(ruleId))
	# END: New methods (Amasty reward extension)





	def getBalance(self, email):
		res = self._getData('mwRewardpoints/getBalanceByEmail/'+email+'/0')

		m = re.search('^Customer email \(([^\)]*)\) has ([0-9]*) reward points', res)
		if m:
			return int(m.group(2))
		else:
			return False

	def setBalance(self, email, points, msg = "Odoo"):
		#data = self.call('rewardpoints.getcustomeridbyemail', [email, 1])
		res = self._getData('mwRewardpoints/getCustomerIdByEmail/'+email+'/0')
		m = re.search('^Customer email \(([^\)]*)\) has customer ID = ([0-9]*)', res)

		try:
			customerId = m.group(2)
			ret = self._getData('mwRewardpoints/updatePoints/'+customerId+'/'+str(points)+'/'+msg)
			return ret
		except Exception as e:
			return False

	def createCustomer(self, email, name, posName):
		groupId = 1

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
		res = self._postData('customers', customer)
		#print(res)

		#self.setBalance(email, 75, 'Registered in Odoo POS');
		mCustomer = self.getCustomerByEmail(email)
		self.add(self, mCustomer["id"], 75, "Registro en tienda.")

		return res

	def getProductPoints(self, sku):
		res = self._getData('mwRewardpoints/getProductRewardPoints/'+sku)
		m = re.search('^Product SKU \(([^\)]*)\) has ([0-9]*) reward points', res)

		if m == None:
			points = 0
		else:
			points = int(m.group(2))

		return points

	def findProductByBarcode(self, barcode):
		product_obj = env['product.product']
		cursor = product_obj.search_read([('barcode', '=', barcode)])
		for product in cursor:
			print (".")

	def searchCustomer(self, email):
		url = "customers/search?searchCriteria[filterGroups][0][filters][0][field]=email&searchCriteria[filterGroups][0][filters][0][value]="+email

		result = self._getData(url)
		if result['total_count'] == 0:
			return False
		else:
			return result['items'][0]





client = Fichas('https://zacatrus.es/rest/all/V1/', 'zaca24', 'carracacosa1')

#res = client.createCustomer('sergio_fichas@infovit.net', 'Sergio', 'Madrid')
#amount = client.getBalance('sergio_fichas@infovit.net')
#client.setBalance('sergio@infovit.net', 100, 'pruebas')
res = client.getPoints(1)
#res = client.getProductPoints('ZAC011')
#res = client.searchCustomer('sergio@infovit.net')
print( res )