# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'
    
    payment_ids = fields.One2many("pos.payment", 'pay_session_id', compute="_compute_payments", store=True)
    payment_group_method_ids = fields.One2many('pos.payment_group_method', 'session_id', store=True, 
                                               compute="_compute_payments")
        
    @api.depends('order_ids.payment_ids', 'order_ids.payment_ids.payment_method_id', "order_ids.payment_ids.amount")
    def _compute_payments(self):
        for r in self:
            payment_method_ids = []
            payment_group_method = {}
            payment_ids = []
            for order in r.order_ids:
                for payment in order.payment_ids:
                    payment_ids.append(payment.id)
                    
                    payment_method_ids.append(payment.payment_method_id.id)
                    key = str(payment.payment_method_id.id)
                    if key not in payment_group_method:
                        payment_group_method.update({key: 0})
                        
                    payment_group_method[key] += payment.amount
                    
            r.payment_ids = [(6, 0, payment_ids)]
                    
            groups_method = self.env['pos.payment_group_method'].search([
                ('session_id', '=', r.id),
                ('payment_method_id', 'not in', payment_method_ids)
            ])
            groups_method.unlink()
                
            for payment_method_id, total in payment_group_method.items():
                payment_group = self.env['pos.payment_group_method'].search([
                    ('session_id', '=', r.id),
                    ('payment_method_id', '=', int(payment_method_id))
                ])
                
                if payment_group:
                    payment_group.write({'importe': total})
                else:
                    self.env['pos.payment_group_method'].create({
                        'session_id': r.id,
                        'payment_method_id': int(payment_method_id),
                        'importe': total
                    })
                    
                    
class PosPaymentGroupMethod(models.Model):
    _name = 'pos.payment_group_method'
    _description = "Pagos agrupados por métodos de pago"
    
    session_id = fields.Many2one('pos.session', string="Sesión")
    payment_method_id = fields.Many2one("pos.payment.method", string="Métodos de pago")
    importe = fields.Monetary("Total")
    currency_id = fields.Many2one("res.currency", related="session_id.currency_id")