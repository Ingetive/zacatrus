# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    @api.model
    def action_replenish_external(self, orderpoint_id):
        orderpoint = self.sudo().browse(id)
        if orderpoint:
            return orderpoint.action_replenish()