# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_box = fields.Integer('Productos por caja')
    x_deposito = fields.Boolean('Deposito')
    x_discontinued = fields.Boolean('Descatalogado')
    x_sku = fields.Char('SKU')
