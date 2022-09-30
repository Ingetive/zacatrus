# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AmazonAccount(models.Model):
    _inherit = 'amazon.account'
    
    def _process_order_lines(self, items_data, shipping_code, shipping_product, currency, fiscal_pos, marketplace_api_ref):
        values = super()._process_order_lines(items_data, shipping_code, shipping_product, currency, fiscal_pos, marketplace_api_ref)
        values.update({'route_id': 58}) # Ruta -> Segovia: Entregar en 2 pasos (Empaquetado + Enviar) Amazon
        return values