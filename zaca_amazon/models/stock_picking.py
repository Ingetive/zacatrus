# -*- coding: utf-8 -*-

import logging

from odoo import models, fields

class Picking(models.Model):
    _inherit = 'stock.picking'
    x_amz_shipping_id = fields.Char()
