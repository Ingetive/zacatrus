# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models
from datetime import datetime

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pt_last_order = fields.Integer(readonly=False)

    last_tarjezaca_date = fields.Date(string="Last proccessed date")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
 
        res.update(
            pt_last_order = self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.pt_last_order'),
            last_tarjezaca_date = self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.last_tarjezaca_date'),
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.pt_last_order', self.pt_last_order)
        self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.last_tarjezaca_date', self.last_tarjezaca_date)

        super(ResConfigSettings, self).set_values()

    def getLastTarjezacaDate(self):
        date = self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.last_tarjezaca_date')
        if date:
            return datetime.strptime(date, '%Y-%m-%d')
        
        return False
    
    def setLastTarjezacaDate(self, date):
        return self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.last_tarjezaca_date', date.strftime("%Y-%m-%d"))