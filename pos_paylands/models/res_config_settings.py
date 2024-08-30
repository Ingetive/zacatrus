# -*- coding: utf-8 -*-

import logging, os
from odoo import api, fields, models
from datetime import datetime

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    paylands_sandbox_mode = fields.Boolean("Paylands en modo pruebas")
    paylands_signature = fields.Char("Firma digital")
    paylands_apikey = fields.Char("Api key")
    last_paylands_date = fields.Date(string="Last proccessed date")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        paylandsSandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_sandbox_mode')
        paylandsSignature = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_signature')
        paylandsApikey = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_apikey')
        last_paylands_date = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_paylands_date')
        res.update(
            paylands_sandbox_mode = paylandsSandboxMode,
            paylands_signature = paylandsSignature,
            paylands_apikey = paylandsApikey,
            last_paylands_date = last_paylands_date
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_sandbox_mode', self.paylands_sandbox_mode)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_signature', self.paylands_signature)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_apikey', self.paylands_apikey)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.last_paylands_date', self.last_paylands_date)

        super(ResConfigSettings, self).set_values()


    def getLastPaylandsDate(self):
        date = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_paylands_date')
        if date:
            return datetime.strptime(date, '%Y-%m-%d')
        
        return False
    
    def setLastPaylandsDate(self, date):
        return self.env['ir.config_parameter'].sudo().set_param('pos_paylands.last_paylands_date', date.strftime("%Y-%m-%d"))

    def getPaylandsApiKey(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_apikey')
        if value:
            if not odooEnv or odooEnv == 'staging':
                if value.find('[test]') == -1:
                    _logger.error(f"Zacalog: odooEnv: {odooEnv}; paylandsApikey: {value}; [test] string not found in paylandsApikey.")
                else:
                    return value.replace("[test]", "")
            else:
                return value
            
        return False