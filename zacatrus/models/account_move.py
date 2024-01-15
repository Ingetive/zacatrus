# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.model
    def registrar_pago(self, move_ids, amount, journal_id=None):
        moves = self.sudo().browse(move_ids)
        if not moves:
            return False
        
        payment_register = self.env['account.payment.register'].with_context({
            'active_model': 'account.move',
            'amount': amount,
            'active_ids': [(6, 0, moves.ids)],
        }).create({})
        
        if journal_id:
            payment_register.write({'journal_id': journal_id})
            
        payment_register.action_create_payments()
        return True
        