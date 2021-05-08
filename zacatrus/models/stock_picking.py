# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Picking(models.Model):
    _inherit = 'stock.picking'

    x_tracking = fields.Char("Numero de tracking de la mensajeria")
