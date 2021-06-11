# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    almacen = fields.Char(related='stock_move_id.warehouse_id.name', string="Almacén")
    ubicacion_origen = fields.Char(related='stock_move_id.location_id.complete_name', string="Ubicación origen")
    ubicacion_destino = fields.Char(related='stock_move_id.location_dest_id.complete_name', string="Ubicación destino")
