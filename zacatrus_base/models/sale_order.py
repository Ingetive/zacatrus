# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.model
    def create_invoices(self):
        daysAgo = datetime.datetime.now() - datetime.timedelta(days=2)

        orders = self.env['sale.order'].search([
            ('date_order', '>', daysAgo),
            ('invoice_status', '=', 'to invoice'),
        ], limit=100)

        for order in orders:
            pickings = self.env['stock.picking'].sudo().search_read([
                ('sale_id', '=', order.id)
            ], ['state'])

            sent = False
            for picking in pickings:
                if picking['state'] == 'done':
                    sent = True
                else:
                    sent = False
                    break
                _logger.error(f"Zacalog: {order['name']} {picking['state']}")

            if sent:
                adv_wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=[order.id]).create({
                  'advance_payment_method': 'delivered'
                })
                act = adv_wiz.create_invoices()

                # Confirm invoice. From draft to posted (publicado)
                iorder = self.env['sale.order'].sudo().browse(order.id)
                for invoiceId in iorder["invoice_ids"]:
                    invoiceId.action_post()