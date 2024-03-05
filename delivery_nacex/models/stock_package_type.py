# -*- coding: utf-8 -*-
# © 2024 Voodoo - <hola@voodoo.es>

from odoo import fields, models


class PackageType(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[('nacex', 'Nacex')])