#!/usr/bin/env python
# coding: utf-8

import re
import json
import requests

url = 'https://zacatrus.es/'
apiuser = 'odoo'
apipass = 'p9U4Lap0vF'

import string
import random



def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))


class Fichas():
	def __init__(self, url, username, password):
		self.username = username
		self.password = password
		self.url = url

	def _getToken(self):
		data = {"username":self.username,"password": self.password}

		response = requests.post(self.url + 'integration/admin/token', json=data, headers={})
		return response.json()

	def _getData(self, url):
		hed = {'Authorization': 'Bearer ' + self._getToken()}

		#url = 'https://api.xy.com'
		response = requests.get(self.url + url, json={}, headers=hed)
		return response.json()

	def _postData(self, url, data):
		hed = {'Authorization': 'Bearer ' + self._getToken()}

		#url = 'https://api.xy.com'
		response = requests.post(self.url + url, json=data, headers=hed)
		return response.json()

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
		self.setBalance(email, 75, 'Registered in Odoo POS');

		return res

	def getProductPoints(self, sku):
		res = self._getData('mwRewardpoints/getProductRewardPoints/'+sku)
		m = re.search('^Product SKU \(([^\)]*)\) has ([0-9]*) reward points', res)

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





client = Fichas('https://zacatrus.es/rest/V1/', 'odoo', 'p9U4Lap0vF')

#res = client.createCustomer('sergio_fichas@infovit.net', 'Sergio', 'Madrid')
#amount = client.getBalance('sergio_fichas@infovit.net')
#client.setBalance('sergio@infovit.net', 100, 'pruebas')
res = client.getBalance('sergio@infovit.net')
#res = client.getProductPoints('ZAC011')
#res = client.searchCustomer('sergio@infovit.net')
print( res )