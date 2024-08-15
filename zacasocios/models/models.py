import re
import json
import requests
import string
import random
import sys
import logging
from datetime import datetime
import pytz
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
		self.cleanMessages()
		
		#self.queueFichasUpdate('sergio@infovit.net', False, "Prueba de fichas", 29.35, "Sergio Viteri", "Chamberi")
		#self.queueFichasUpdate('sergio@infovit.net', -52, "Prueba de fichas gastadas", False, "Tal")
		lastOrder = int(self.env['ir.config_parameter'].sudo().get_param('zacasocios.last_order'))
		fichasProduct = self.env['ir.config_parameter'].sudo().get_param('zacasocios.fichas_product_id')

		if not lastOrder or not fichasProduct:
			_logger.warning("Zacasocios: Please, configure Zacasocios module.")
		else:
			prevLastOrder = lastOrder
			args = [('id', '>', prevLastOrder)]
			posOrders = self.env['pos.order'].search_read (args, limit=20, order='create_date asc')
			for posOrder in posOrders:
				sessions = self.env['pos.session'].search_read([('id', '=', posOrder['session_id'][0])])
				posName = ""
				for session in sessions:
					posName = session["config_id"][1]
					
				partnerEmail = None
				partnerName = None
				if posOrder['partner_id']:
					#_logger.warning(f"Zacalog: zacasocios: {posOrder['partner_id']}")
					partners = self.env['res.partner'].search_read([('id', '=', posOrder['partner_id'][0])])
					for partner in partners:
						partnerEmail = partner['email']
						partnerName = partner['name']
				if partnerEmail:
					iargs = [("order_id", "=", posOrder['id'])]
					posOrdersItems = self.env['pos.order.line'].search_read(iargs)
					for posOrdersItem in posOrdersItems:
						#_logger.warning(f"Zacalog: zacasocios: args")
						args = [('id', '=', posOrdersItem['product_id'][0] )]
						products = self.env['product.product'].search_read(args)
						#_logger.warning(f"Zacalog: zacasocios: sustract {products[0]['id']} == {fichasProduct}")
						if products[0]['id'] == int(fichasProduct):
							if (posOrdersItem['qty']):
								#_logger.warning(f"Zacalog: zacasocios: sustract {posOrdersItem['qty']}")
								self._sustractFichas(partnerEmail, posOrdersItem['qty'], partnerName, posName)

					#Gift cards don't give points
					fichasToAdd = posOrder['amount_total']
					tarjezacaProductId = int(self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.card_product_id'))
					if tarjezacaProductId:
						giftCardAmount = 0
						for posOrdersItem in posOrdersItems:
							if int(posOrdersItem["product_id"][0]) == int(tarjezacaProductId):
								giftCardAmount += posOrdersItem["price_subtotal_incl"]
						fichasToAdd -= giftCardAmount

					if fichasToAdd > 0:
						self._addFichas(partner, fichasToAdd, posName)
						
				if prevLastOrder < posOrder["id"]:
					prevLastOrder = posOrder["id"]
					#_logger.warning(f"Zacalog: zacasocios: setting prevLastOrder {prevLastOrder}")
					self.env['ir.config_parameter'].sudo().set_param('zacasocios.last_order', posOrder["id"])
                    #self.env['ir.config_parameter'].sudo().set_values()

		blockQueue = self.env['ir.config_parameter'].sudo().get_param('zacasocios.block_magento_sync')	
		if not blockQueue:
			self.procFichasUpdateQueue()            
	
	def _sustractFichas(self, email, qty, name, posName = False):
		if qty < 0:
			msg = "Canjeados en tienda"
		else:
			msg = "Devolución en tienda"

		self.queueFichasUpdate(email, qty, msg, False, name, posName)

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

	def procFichasUpdateQueue(self):
		increase = False

		now = datetime.now(pytz.timezone('Europe/Madrid')).time()
		if now.hour < 6:
			increase = True
		#_logger.warning(f"Zacalog: hour is {now.hour}")


		args = []
		if not increase:
			args.append( ('qty', '<', 0) )
		queue = self.env['zacasocios.queue'].search( args, limit=20, order='create_date asc' )

		for item in queue:
			if item.attempts < MAX_ATTEMPTS:
				ok = False
				try:
					ok = self._procFichasItem(item, increase)
				except Exception as e:
					ok = False

				if not ok:
					msg = f"Failed updating points: {item['email']} {item['qty']} {item['spent']}"

					#db.fichas_queue.bulk_write([ DeleteOne({"_id": item["_id"]}) ])
					self.env['zacatrus_base.notifier'].error("zacasocios.queue", item.id, msg)
					#item.unlink()
					
					item.write({"attempts": item.attempts + 1})

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
		magento = self.env['zacatrus.connector']

		try:
			customer = magento.getCustomerByEmail(item.email.strip())
			if not customer:
				if item.name and item.email and item.pos:
					customer = magento.createCustomer(item.email.strip(), item.name, item.pos)

		except Exception as e:
			customer = None

		return customer

	def _getPoints(self, item):
		magento = self.env['zacatrus.connector']

		if not item.qty and item.spent:
			rule = magento.getRule()
			if not rule:
				return False
			points = int(item.spent * rule["amount"]/rule["spent_amount"])
		else:
			points = item.qty

		return points

	def _procFichasItem(self, item, increase):
		magento = self.env['zacatrus.connector']
		ok = False

		if self._isAnIncrease(item):
			if increase:
				customer = self._getCustomer(item)
				if customer:
					points = self._getPoints(item)
					ok = magento.doAdd(customer['id'], points, item.msg)
			else:
				return True
		else:
			customer = self._getCustomer(item)
			if customer:
				points = self._getPoints(item)
				ok = magento.doDeduct(customer['id'], (-1)*points, item.msg)
				if not ok and points < 0:
					left = magento.doDeductBlocks(customer['id'], (-1)*points, item.msg)
					if left <= 0:
						ok = True
					else:
						if ((-1)*left) != points:
							msg = f"Fichas parcialmente descontadas. Solicitado: {points}; Sin hacer: {left}"
							_logger.error("Zacalog: {msg}")
							self.env['zacatrus_base.notifier'].error("zacasocios.queue", item.id, msg)
							item.write({"qty": (-1)*left})

		if ok:
			item.unlink()

		return ok

	def cleanMessages(self):
		messages = self.env['mail.message'].search([('model', '=', 'zacasocios.queue')])
		for msg in messages:
			count = self.env['zacasocios.queue'].search_count([('id', '=', msg.res_id)])
			if count == 0:
				msg.unlink()