# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_box = fields.Integer('Productos por caja')
    x_embalaje = fields.Integer('Unidad de embalaje (ECI)')
    x_deposito = fields.Boolean('Deposito')
    x_discontinued = fields.Boolean('Descatalogado')
    x_sku = fields.Char('SKU')
    x_manufacturer = fields.Char('Editorial')
    x_box_discount_percent = fields.Float(
        string="Descuento por caja (%)",
        help="Porcentaje de descuento aplicado cuando compran cajas enteras",
        default=0.0,
    )
