# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, time, datetime


class pos_config(models.Model):
    _inherit = 'pos.config'

    pos_logo = fields.Binary(string='POS Logo')
    show_barcode = fields.Boolean(string="Show Barcode")
     

class pos_order_inherit(models.Model):
	_inherit = "pos.order"

	barcode_number = fields.Char(string="Barcode Number")

	@api.model
	def _order_fields(self, ui_order):
		res = super(pos_order_inherit, self)._order_fields(ui_order)
		res['barcode_number'] = ui_order['barcode']
		return res	