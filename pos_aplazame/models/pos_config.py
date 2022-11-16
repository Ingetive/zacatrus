# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class PosConfig(models.TransientModel):
    _inherit = 'res.config'

    x_aplazame_key = fields.Char("Aplazame private api key")