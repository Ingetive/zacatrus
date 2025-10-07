# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    x_box_discount_applied = fields.Boolean(
        string="Descuento por caja aplicado.",
        readonly=True,
        help="Indica si el descuento por caja se ha aplicado automáticamente.",
    )
    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrderLine, self).create(vals_list)
        for record in res:
            if record.order_id.team_id.id == 14 and record.product_id.id != self.env.ref("sale_amazon.shipping_product").id:  # Equipo de venta -> Amazon
                record.write({'route_id': 58})  # Ruta -> Segovia: Entregar en 2 pasos (Empaquetado + Enviar) Amazon
        return res

    def _compute_should_apply_box_discount(self):
        self.ensure_one()
        product = self.product_id
        if not product:
            return False
        tmpl = product.product_tmpl_id
        size = tmpl.x_box or 0
        if not size or tmpl.x_box_discount_percent <= 0:
            return False
        qty = self.product_uom_qty
        # Condition: quantité strictement multiple de la taille de boîte
        return qty and size and (qty % size == 0)


    def _apply_or_reset_box_discount(self):
        for line in self:
            if line.display_type:
                continue
            if line._compute_should_apply_box_discount():
                percent = line.product_id.product_tmpl_id.x_box_discount_percent
                line.update({
                    "discount": percent,
                    "x_box_discount_applied": True,
                })
            else:
            # On ne remet à zéro que si c’était notre remise auto
                if line.x_box_discount_applied:
                    line.update({
                        "discount": 0.0,
                        "x_box_discount_applied": False,
                    })


    @api.onchange("product_id", "product_uom_qty")
    def _onchange_box_discount(self):
        self._apply_or_reset_box_discount()

    @api.model
    def create(self, vals):
        line = super().create(vals)
        line._apply_or_reset_box_discount()

        return line

    def write(self, vals):
        res = super().write(vals)
        # Si la quantité ou le produit changent, on recalcule
        keys = set(vals.keys())
        if {"product_id", "product_uom_qty"} & keys:
            for line in self:
                line._apply_or_reset_box_discount()

        return res