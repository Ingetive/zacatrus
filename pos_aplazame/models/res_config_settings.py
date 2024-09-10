# -*- coding: utf-8 -*-

import logging, os
from odoo import api, fields, models
from datetime import datetime

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aplazame_sandbox_mode = fields.Boolean("Aplazame en modo pruebas")
    aplazame_notification_url = fields.Char("Url para notificaciones de Aplazame")
    last_aplazame_date = fields.Date()
    aplazame_api_key = fields.Char()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        aplazameSandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_sandbox_mode')
        aplazameIpnUrl = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_notification_url')
        lastAplazameDate = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.last_aplazame_date')
        aplazameApiKey = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_api_key')
        res.update(
            aplazame_sandbox_mode = aplazameSandboxMode,
            aplazame_notification_url = aplazameIpnUrl,
            last_aplazame_date = lastAplazameDate,
            aplazame_api_key = aplazameApiKey
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.aplazame_sandbox_mode', self.aplazame_sandbox_mode)
        self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.aplazame_notification_url', self.aplazame_notification_url)
        self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.last_aplazame_date', self.last_aplazame_date)
        self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.aplazame_api_key', self.aplazame_api_key)

        super(ResConfigSettings, self).set_values()


    def getLastAplazameDate(self):
        date = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.last_aplazame_date')
        if date:
            return datetime.strptime(date, '%Y-%m-%d')
        
        return False
    
    def setLastAplazameDate(self, date):
        return self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.last_aplazame_date', date.strftime("%Y-%m-%d"))
    
    def getAplazameApiKey(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_api_key')
        if value:
            if not odooEnv or odooEnv == 'staging':
                if value.find('[test]') == -1:
                    _logger.error(f"Zacalog: odooEnv: {odooEnv}; aplazame_api_key: {value}; [test] string not found in aplazame_api_key.")
                else:
                    return value.replace("[test]", "")
            else:
                return value
            
        return False