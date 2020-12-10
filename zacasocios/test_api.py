#!/usr/bin/env python
# coding: utf-8

import requests
import sys
import re
import string
import random

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

class Fichas():
	apiuser = ''
	apipass = ''
	url = ''

	def __init__(self, url, username, password):
		self.url = url
		self.apiuser = username
		self.apipass = password

	def _getToken(self):
		data = {"username": self.apiuser, "password": self.apipass}
		url = self.url + "/rest/V1/integration/admin/token"
		response = requests.post(url, json=data)
		return response.json()

	def getBalance(self, email):
		url = self.url + "/rest/V1/mwRewardpoints/getBalanceByEmail/"+email+"/0"
		hed = {'Authorization': 'Bearer ' + self._getToken()}
		response = requests.get(url, headers=hed)
		m = re.search('^Customer email \(([^\)]*)\) has ([0-9]*) reward points', response.json())
		if m:
			return (int(m.group(2)))
		return False

	def searchCustomer(self, email):
		url = self.url + "/rest/V1/mwRewardpoints/getCustomerIdByEmail/"+ email +"/0"
		hed = {'Authorization': 'Bearer ' + self._getToken()}
		response = requests.get(url, headers=hed)
		m = re.search('not avail?able', response.json())
		if m:
			return False
		m = re.search('^Customer email \(([^\)]*)\) has customer ID = ([0-9]*)', response.json())
		if m:
			return (int(m.group(2)))
		
		return False

	def setBalance(self, email, points, msg = "Odoo"):
		userId = self.searchCustomer(email)
		url = self.url + "/rest/V1/mwRewardpoints/updatePoints/"+str(userId)+"/"+str(points)+"/"+msg
		hed = {'Authorization': 'Bearer ' + self._getToken()}
		response = requests.get(url, headers=hed)

		return False

	def getProductPoints(self, sku):
		url = self.url + "/rest/V1/mwRewardpoints/getProductRewardPoints/"+sku+""
		hed = {'Authorization': 'Bearer ' + self._getToken()}
		response = requests.get(url, headers=hed)

		print (response.json())
		m = re.search('^Product sku \(([^\)]*)\) has ([0-9]*) reward points', response.json(), re.IGNORECASE)

		points = 0
		if m:
			return int(m.group(2))

		return False

	def createCustomer(self, email, name, posName):
		group_id = 1

		_m = re.search('adrid', posName)
		if _m:
			group_id = 18
		_m = re.search('evilla', posName)
		if _m:
			group_id = 19
		_m = re.search('alencia', posName)
		if _m:
			group_id = 20

		url = self.url + "/rest/V1/customers"

		hed = {'Authorization': 'Bearer ' + self._getToken()}
		data = {'customer': {
			'email': email,
			'firstname': name,
			'lastname': '.',
			#'password': id_generator(),
			'website_id': '1',
			'group_id': group_id
		}}
		response = requests.post(url, json=data, headers=hed)
		
		#print(response.json())

		self.setBalance(email, 75, 'Registered in Odoo POS');

		return True




magento_client = Fichas('https://zacatrus.es', 'odoo', 'p9U4Lap0vF')
magento_client.setBalance('sergio@infovit.net', 1000)
number = magento_client.getBalance('sergio@infovit.net')
print(number)
number = magento_client.searchCustomer('sergio@infovit.net')
print(number)
number = magento_client.getProductPoints("ZAC006")
print(number)
magento_client.createCustomer("unoinventado4@infovit.net", "uno", "Sevilla")