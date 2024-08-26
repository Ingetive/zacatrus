# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class EdiError(models.Model):
    _name = 'zacaedi.error'
    _description = 'Guarda los posibles errores que se producen al importar pedidos EDI'
    
    code = fields.Integer(readonly=False)
    origin = fields.Char(readonly=False)
    message = fields.Char(readonly=False)
    bundle_id = fields.Many2one("zacaedi.bundle", string="Bundle")