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
		

