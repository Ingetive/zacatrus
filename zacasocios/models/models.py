import re
import json
import requests
import string
import random
import sys
import logging
import hmac, base64, struct, hashlib, time, os

_logger = logging.getLogger(__name__)

from odoo import models, fields, api
MAX_ATTEMPTS = 10

class FichaQueue(models.Model):
	_name = 'zacasocios.queue'
	_description = 'Cola de Fichas a actualizar'

	email = fields.Char(string='email')
	name = fields.Char(string='name')
	pos = fields.Char(string='pos')
	qty = fields.Integer(string='qty')
	msg = fields.Char(string='msg')
	spent = fields.Float(string='spent')
	attempts = fields.Integer(string='attempts')

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
		fichasProductId = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.fichas_product_id')

		client_obj = self.env['res.partner']
		pos_obj = self.env['pos.order']
		pos_item_obj = self.env['pos.order.line']
		product_obj = self.env['product.product']
		cursor = client_obj.search_read([('email', '=', email)])
		for _client in cursor:
			#args = [('state', '<>', "done" ),('partner_id', '=', _client["id"] )]
			args = [('state', 'not in', ['done', 'invoiced']),('partner_id', '=', _client["id"] )]
			pos = pos_obj.search_read(args)
			for po in pos:
				iargs = [("order_id", "=", po['id'])]
				posOrdersItems = pos_item_obj.search_read(iargs)
				for item in posOrdersItems:
					if int(fichasProductId) == int(item['product_id'][0]):
						if (item['qty'] and item['qty'] < 0):
							return True

		return False

	@api.model
	def getBalance( self, email, posName ):
		zacatrus = self.env['zacatrus.connector']

		fichas = 0
		if not self._isEmployee( email ) and not self._clientAlreadySpent(email):
			fichas = zacatrus.getBalance(email)

		return fichas

	@api.model
	def getFichasProductId( self ):
		fichasProductId = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.fichas_product_id')

		if (fichasProductId):
			return int(fichasProductId)
		else:
			return False
		
	def sync(self):
		lastOrder = self.env['ir.config_parameter'].sudo().get_param('zacasocios.last_order')
		fichasProduct = self.env['ir.config_parameter'].sudo().get_param('zacasocios.fichas_product_id')

		if not lastOrder or not fichasProduct:
			_logger.warning("Zacasocios: Please, configure Zacasocios module.")
		else:
			args = [('id', '>', lastOrder)]
			posOrders = self.env['pos.order'].search_read (args)
			for posOrder in posOrders:
				partnerEmail = None
				if posOrder['partner_id']:
					partners = self.env['res.partner'].read(posOrder['partner_id'][0])
					for partner in partners:
						partnerEmail = partner['email']
				if partnerEmail:
					iargs = [("order_id", "=", posOrder['id'])]
					posOrdersItems = self.env['pos.order.line'].search_read(iargs)
					for posOrdersItem in posOrdersItems:
						args = [('id', '=', posOrdersItem['product_id'][0] )]
						products = self.env['product.product'].search_read(args)
						if(products[0]['id'] == fichasProduct.id): #OJO: revisar
							if (posOrdersItem['qty']):
								self._sustractFichas(partnerEmail, posOrdersItem['qty'])

					sessions = self.env['pos.session'].read(posOrder['session_id'][0])
					posName = ""
					for session in sessions:
						posName = session["config_id"][1]

					#Gift cards don't give points
					fichasToAdd = posOrder['amount_total']
					tarjezacaProductId = self.getGiftCardProductId()
					if tarjezacaProductId:
						giftCardAmount = 0
						for posOrdersItem in posOrdersItems:
							if int(posOrdersItem["product_id"][0]) == int(tarjezacaProductId):
								giftCardAmount += posOrdersItem["price_subtotal_incl"]
						fichasToAdd -= giftCardAmount

					if self.verbose:
						print("Adding Fichas... "+ str(fichasToAdd))
					if fichasToAdd > 0:
						self._addFichas(partner, fichasToAdd, posName)
						
				if prevLastOrder < posOrder["id"]:
					prevLastOrder = posOrder["id"]
					self.env['ir.config_parameter'].sudo().set_param('zacasocios.fichas_product_id', posOrder["id"])
					
	def _sustractFichas(self, email, qty):
		if qty < 0:
			msg = "Canjeados en tienda"
		else:
			msg = "Devolución en tienda"

		self.queueFichasUpdate(email, qty, msg)

	def _addFichas(self, partner, spent, posName = False):
		if spent > 0:
			msg = "Compra en tienda"
		else:
			msg = "Devolución en tienda"

		self.queueFichasUpdate(partner['email'], False, msg, spent, partner['name'], posName)

	def queueFichasUpdate(self, email, qty, msg = "Modificado por el administrador", spent = False, name = False, pos = False):
		if not spent and qty == 0:
			return
		
		item = self.env['zacasocios.queue'].create({
			'email': email, 'name': name, 'pos': pos, 'qty': qty, 'msg': msg, 
			'spent': spent, 'attempts': 0
		})

		return item

	def procFichasUpdateQueue(self, increase):
		args = []
		queue = self.env['zacasocios.queue'].search( args, limit=100, order='create_date asc' )

		for item in queue:
			ok = False
			try:
				ok = self._procFichasItem(item, increase)
			except Exception as e:
				ok = False

			if not ok:
				attempts = MAX_ATTEMPTS
				if 'attempts' in item:
					attempts = item.attempts +1

				if attempts >= MAX_ATTEMPTS:
					msg = f"Failed updating points: {item['email']} {item['qty']} {item['spent']}"

					#db.fichas_queue.bulk_write([ DeleteOne({"_id": item["_id"]}) ])
					self.env['zacatrus_base.notifier'].error("zacasocios.queue", item.id, msg)
					item.unlink()
				else:
					item.write({"attempts": attempts})

		return True

	def _isAnIncrease(self, item):
		isAnIncrease = False

		if not item.qty and item.spent:
			if item.spent > 0:
				isAnIncrease = True
		else:
			if item.qty > 0:
				isAnIncrease = True

		return isAnIncrease
    
	def _getCustomer(self, item):
		customer = None

		try:
			customer = self.magento.getCustomerByEmail(item['email'].strip())
			if not customer:
				if 'name' in item and item['name'] and item['pos']:
					customer = self.magento.createCustomer(item['email'].strip(), item['name'], item['pos'])

		except Exception as e:
			customer = None

		return customer

	def _getPoints(self, item):
		if not item['qty'] and item['spent']:
			rule = self.magento.getRule()
			if not rule:
				return False
			points = int(item['spent'] * rule["amount"]/rule["spent_amount"])
		else:
			points = item["qty"]

		return points

	def _procFichasItem(self, item, increase):
		db =  self._getMongoDb()
		ok = False

		if self._isAnIncrease(item):
			if increase:
				customer = self._getCustomer(item)
				if customer:
					points = self._getPoints(item)
					if self.verbose:
						print (f"Adding {points} points to {item['email']}")
					ok = self.magento.doAdd(customer["id"], points, item["msg"])
			else:
				return True
		else:
			customer = self._getCustomer(item)
			if customer:
				points = self._getPoints(item)
				ok = self.magento.doDeduct(customer["id"], (-1)*points, item["msg"])
				if not ok and points < 0:
				#self._getSlack().sendWarn( f"Failed deducting {points} points to {item['email']}. Trying blocks...", "C02211VKDKM" ) #TODO: remove when stable
					ok = self.magento.doDeductBlocks(customer["id"], (-1)*points, item["msg"])

		if ok:
			item.unlink()

		return ok

