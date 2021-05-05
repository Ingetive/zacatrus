# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    x_partner_id8 = fields.Char("Id. en Odoo 8")
