# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'
    
    payment_ids = fields.One2many("pos.payment", 'pay_session_id', compute="_compute_payments")
    
    @api.depends('order_ids.payment_ids')
    def _compute_payments(self):
        for r in self:
            payment_ids = []
            for order in r.order_ids:
                payment_ids += order.payment_ids.ids

            r.payment_ids = [(6, 0, payment_ids)]