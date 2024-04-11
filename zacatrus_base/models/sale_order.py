# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    
    @api.model
    def create_invoices(self):
        fecha_hace_2_dias = datetime.datetime.now() - datetime.timedelta(days=2)

        pedidos_a_facturar = env['sale.order'].search([
            ('date_order', '>', fecha_hace_2_dias),
            ('invoice_status', '=', 'to invoice'),
        ], limit=100)

        for pedido in pedidos_a_facturar:
            pickings = self.env['stock.picking'].sudo().search_read([
                ('sale_id', '=', pedido.id)
            ], ['state'])

            sent = False
            for picking in pickings:
                _logger.debug("Zacalog:  " + picking['state'])

            #adv_wiz = env['sale.advance.payment.inv'].with_context(active_ids=[pedido.id]).create({
            #  'advance_payment_method': 'delivered'
            #})
            #act = adv_wiz.create_invoices()