# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    x_partner_id8 = fields.Char("Id. en Odoo 8")
