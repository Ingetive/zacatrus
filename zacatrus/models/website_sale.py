# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleBoxDiscount(WebsiteSale):
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kw):
        res = super()._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, **kw)
        order = http.request.website.sale_get_order()
        if order:
            # On réapplique la logique de remise boîte pour toutes les lignes
            order.order_line._apply_or_reset_box_discount()
        return res
