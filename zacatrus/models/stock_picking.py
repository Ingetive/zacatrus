# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Picking(models.Model):
    _inherit = 'stock.picking'

    x_tracking = fields.Char("Numero de tracking de la mensajeria")
    x_status = fields.Integer('Estado de sincronización')
    partner_zip = fields.Char(related="partner_id.zip", store=True)
