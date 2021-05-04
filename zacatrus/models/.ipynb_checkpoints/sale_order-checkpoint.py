# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_company = fields.Char("Empresa")
    x_droppoint = fields.Integer('Punto Nacexshop')
