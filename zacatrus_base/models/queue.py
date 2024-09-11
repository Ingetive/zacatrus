# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class Queue(models.Model):
    _name = 'zacatrus_base.queue'
    _description = 'Cola de productos a actualizar stock.'
    
    sku = fields.Char()
    qty = fields.Integer()
    relative = fields.Boolean()
    last_repo = fields.Date()
    source = fields.Char()