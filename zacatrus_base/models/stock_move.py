# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move']

    x_status = fields.Integer('Estado de sincronización')
