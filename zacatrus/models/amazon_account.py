# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AmazonAccount(models.Model):
    _inherit = 'amazon.account'

    def _prepare_order_lines_values(self, order_data, currency, fiscal_pos, shipping_product):
        """ Inherit sale_amazon/models/amazon_account.py
        """
        res = super()._prepare_order_lines_values(order_data, currency, fiscal_pos, shipping_product)
        if shipping_product.id != self.env.ref("sale_amazon.shipping_product").id:
            res.update({'route_id': 58})  # Ruta -> Segovia: Entregar en 2 pasos (Empaquetado + Enviar) Amazon
        return res