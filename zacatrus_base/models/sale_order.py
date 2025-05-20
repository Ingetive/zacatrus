# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _createInvoice(self, order):
        adv_wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=[order.id]).create({
        'advance_payment_method': 'delivered'
        })
        adv_wiz.create_invoices()

        # Confirm invoice. From draft to posted (publicado)
        iorder = self.env['sale.order'].sudo().browse(order.id)
        for invoiceId in iorder["invoice_ids"]:
            try:
                invoiceId.action_post()
            except:
                pass
    
    @api.model
    def create_invoices(self):
        daysAgo = datetime.datetime.now() - datetime.timedelta(days=15)

        orders = self.env['sale.order'].search([
            ('date_order', '>', daysAgo),
            ('invoice_status', '=', 'to invoice'),
        ], limit=100)

        for order in orders:
            if order.team_id.id in [14,16] and order.amazon_channel == 'fba': #team_id: amazon es o fr
                self._createInvoice(order)
            else:
                pickings = self.env['stock.picking'].sudo().search_read([
                    ('sale_id', '=', order.id),
                    ('state', '!=', 'cancel'),
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
                    self._createInvoice(order)


    @api.model
    def check_stuck(self):
        daysAgo = datetime.datetime.now() - datetime.timedelta(days=1)

        pickings = self.env['stock.picking'].search([
            ('create_date', '>', daysAgo),
            ('state', '=', 'confirmed'),
            ('picking_type_id', 'in', [3,103])
        ], order='create_date DESC', limit=10)

        for picking in pickings:
            if picking['sale_id']:
                moves = self.env['stock.move'].search([
                    ('picking_id', '=', picking.id)
                ], order='create_date DESC')
                available = True
                for move in moves:
                    #print(move.product_id.name, move.product_id.virtual_available)
                    if move.product_id.virtual_available <= 0:
                        available = False
                        break
                if not available:
                    msg = f"El pedido {picking['sale_id'].name} no se ha enviado. Puede que falte stock de algún producto. Por favor, revisar y avisar al cliente si corresponde. Gracias."

                    #print( msg )
                    self.env['zacatrus_base.slack'].sendWarn( msg )