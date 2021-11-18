# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    x_partner_id8 = fields.Char("Id. en Odoo 8")
