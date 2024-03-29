# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    @api.model
    def action_replenish_external(self, orderpoint_id):
        orderpoint = self.env["stock.warehouse.orderpoint"].sudo().browse(orderpoint_id)
        if orderpoint:
            return orderpoint.action_replenish()