# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPayment(models.Model):
    _inherit = 'pos.payment'
    
    pay_session_id = fields.Many2one("pos.session", string="Sesión ")