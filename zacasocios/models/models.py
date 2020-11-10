import re
import json
import requests
import string
import random
import sys

url = 'https://stage.zacatrus.es/rest/V1/' #TODO:Change for production
apiuser = 'odoo'
apipass = 'p9U4Lap0vF'

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

	def add(self, customerId, qty, comment="Añadidos por el administrador", expire=365, action="admin"):
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

	def deduct(self, customerId, qty):
		data = {
			"customer_id": customerId, 
			"amount": qty,
			"comment": "Eliminados por el administrador",
			"action": "admin"
		}
		res = self._getData('rewards/management/points/deduct', data)
		
		return res
		
	def getRule(self, ruleId = 9):
		return self._getData('rewards/management/rule?rule_id=' + ruleId)
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
			file = open("/tmp/zacasocios.log","a")  
			file.write("ERROR: Cannot get product points (sku: %s) from magento.\n" % (sku))
			file.close() 

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


from odoo import models, fields, api
class Zacasocios(models.Model):
	_name = 'zacasocios.zacasocios'

	def _getCustomer(self, email):
		client_obj = self.env['res.partner']
		cursor = client_obj.search_read([('email', '=', email)], ['name', 'property_product_pricelist'])
		for _client in cursor:
			return _client

		return False

	def _isEmployee(self, email):
		client_obj = self.env['res.partner']
		cursor = client_obj.search_read([('email', '=', email)], ['name', 'property_product_pricelist'])
		for _client in cursor:
			_m = re.search('mpleado', _client['property_product_pricelist'][1])
			if _m:
				return True

		return False

	@api.model
	def getBalance( self, email, posName ):
		file = open("/tmp/zacasocios.log","a")  
		file.write("Getting balance 1 for %s \n" % (email))
		file.close() 

		magento_client = Fichas(url, apiuser, apipass)
		if not magento_client.searchCustomer( email ):
			_customer = self._getCustomer(email)
			magento_client.createCustomer(email, _customer['name'], posName)

		if not self._isEmployee( email ):
			#fichas = magento_client.getBalance( email )
			mCustomer = magento_client.getCustomerByEmail(email)
			fichas = magento_client.getPoints( mCustomer["id"] )
		else:
			fichas = 0

		# Log action
		file = open("/tmp/zacasocios.log","a")  
		file.write("Getting balance for %s: %s \n" % (email, fichas))
		file.close() 

		return fichas

	@api.model
	def setBalance( self, email, qty, msg = "Odoo" ):
		if not self._isEmployee(email):
			client = Fichas(url, apiuser, apipass)

			# Log action
			file = open("/tmp/zacasocios.log","a")  
			file.write("Setting balance for %s: %s, %s \n" % (email, qty, msg))
			file.close() 

			#fichas = client.setBalance(email, qty, msg)
			mCustomer = client.getCustomerByEmail(email)
			client.add(self, mCustomer["id"], qty, msg, 365, "moneyspent")

	def findProductByBarcode(self, barcode):
		product_obj = self.env['product.product']
		cursor = product_obj.search_read([('barcode', '=', barcode)], ['name', 'x_sku'])
		for product in cursor:
			return cursor[0]

		return False

	@api.model
	def earnByOrder(self, email, orderInfo):
		client = Fichas(url, apiuser, apipass)
		totalOrderPoints = 0

		_orderInfo = json.loads(orderInfo)
		
		# Log action
		file = open("/tmp/zacasocios.log","a")  
		file.write(orderInfo) 
		file.write("\n") 
 	

		for line in json.loads(orderInfo):
			file.write(str(line)) 
			file.write("\n") 
			if line['barcode']:
				rule = client.getRule()
				qty = line["price"] * rule["amount"]/rule["spent_amount"] * line['quantity']
				#_product = self.findProductByBarcode(line['barcode'])
				#if _product:
				#	points = client.getProductPoints(_product['x_sku'])
				#	if points:
				#		totalOrderPoints = totalOrderPoints + (points * line['quantity'])

		file.write("[1] Setting balance for %s: %s \n" % (email, totalOrderPoints))
		file.close() 
	
		#client.setBalance(email, totalOrderPoints, "[Odoo] Pedido de tienda")
		mCustomer = client.getCustomerByEmail(email)
		client.add(self, mCustomer["id"], totalOrderPoints, "Compra en tienda.", 365, "moneyspent")
		