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
    last_adyen_index = fields.Char()
    last_adyen_pos_index = fields.Char()
    adyen_report_user = fields.Char()
    adyen_report_password = fields.Char()
    global_paylands_signature = fields.Char("Firma digital global")
    global_paylands_apikey = fields.Char("Api key global")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        paylandsSandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_sandbox_mode')
        paylandsSignature = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_signature')
        paylandsApikey = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_apikey')
        last_paylands_date = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_paylands_date')
        last_adyen_index = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_adyen_index')
        last_adyen_pos_index = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_adyen_pos_index')
        adyen_report_user = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.adyen_report_user')
        adyen_report_password = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.adyen_report_password')
        global_paylands_signature = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.global_paylands_signature')
        global_paylands_apikey = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.global_paylands_apikey')
        res.update(
            paylands_sandbox_mode = paylandsSandboxMode,
            paylands_signature = paylandsSignature,
            paylands_apikey = paylandsApikey,
            last_paylands_date = last_paylands_date,
            last_adyen_index = last_adyen_index,
            last_adyen_pos_index = last_adyen_pos_index,
            adyen_report_user = adyen_report_user,
            adyen_report_password = adyen_report_password,
            global_paylands_signature = global_paylands_signature,
            global_paylands_apikey = global_paylands_apikey
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_sandbox_mode', self.paylands_sandbox_mode)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_signature', self.paylands_signature)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_apikey', self.paylands_apikey)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.last_paylands_date', self.last_paylands_date)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.last_adyen_index', self.last_adyen_index)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.last_adyen_pos_index', self.last_adyen_pos_index)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.adyen_report_user', self.adyen_report_user)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.adyen_report_password', self.adyen_report_password)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.global_paylands_signature', self.global_paylands_signature)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.global_paylands_apikey', self.global_paylands_apikey)

        super(ResConfigSettings, self).set_values()


    def getLastPaylandsDate(self):
        date = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_paylands_date')
        if date:
            return datetime.strptime(date, '%Y-%m-%d')
        
        return False
    
    def getLastAdyenReportUser(self):
        return self.env['ir.config_parameter'].sudo().get_param('pos_paylands.adyen_report_user')
    
    def getLastAdyenReportPassword(self):
        return self.env['ir.config_parameter'].sudo().get_param('pos_paylands.adyen_report_password')
    
    def getLastAdyenIndex(self):
        index = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_adyen_index')
        if index:
            return int(index)
        return False
    
    def setLastAdyenIndex(self, index):
        return self.env['ir.config_parameter'].sudo().set_param('pos_paylands.last_adyen_index', index)
    
    def setLastAdyenPosIndex(self, index):
        return self.env['ir.config_parameter'].sudo().set_param('pos_paylands.last_adyen_pos_index', index)
    
    def getLastAdyenPosIndex(self):
        index = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.last_adyen_pos_index')
        if index:
            return int(index)

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

    def getPaylandsGlobalApiKey(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.global_paylands_apikey')
        if value:
            if not odooEnv or odooEnv == 'staging':
                if value.find('[test]') == -1:
                    _logger.error(f"Zacalog: odooEnv: {odooEnv}; paylandsApikey: {value}; [test] string not found in paylandsApikey.")
                else:
                    return value.replace("[test]", "")
            else:
                return value
            
        return False