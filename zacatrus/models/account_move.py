# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.model
    def registrar_pago(self, move_id, journal_id=None):
        move = self.sudo().browse(move_id)
        if not move:
            return False
        
        payment_register = self.env['account.payment.register'].with_context({
            'active_model': 'account.move',
            'active_ids': [move.id],
        }).create({})
        
        if journal_id:
            payment_register.write({'journal_id': journal_id})
            
        payment_register.action_create_payments()
        return True
