# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_mage_category = fields.Char('Categoría en magento')
    x_mage_ocasiones = fields.Char('Ocasiones')
