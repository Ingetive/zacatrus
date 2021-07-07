# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_magento_category = fields.Integer('Categoría en magento')
    x_magento_ocasiones = fields.Boolean('Ocasiones')
