# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aplazame_sandbox_mode = fields.Boolean("Aplazame en modo pruebas")
    aplazame_notification_url = fields.Char("Url para notificaciones de Aplazame")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        aplazameSandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_sandbox_mode')
        aplazameIpnUrl = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_notification_url')
        res.update(
            aplazame_sandbox_mode = aplazameSandboxMode,
            aplazame_notification_url = aplazameIpnUrl,
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.aplazame_sandbox_mode', self.aplazame_sandbox_mode)
        self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.aplazame_notification_url', self.aplazame_notification_url)

        super(ResConfigSettings, self).set_values()
