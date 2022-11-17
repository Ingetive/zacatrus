# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aplazame_sandbox_mode = fields.Boolean("Aplazame en modo pruebas")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        aplazameSandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_aplazame.aplazame_sandbox_mode')
        res.update(
            aplazame_sandbox_mode = aplazameSandboxMode,
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.aplazame_sandbox_mode', self.aplazame_sandbox_mode)
        if self.aplazame_sandbox_mode and self.aplazame_sandbox_mode != "":
            _logger.warning("_TZ: card:"+str(self.aplazame_sandbox_mode))
            self.env['ir.config_parameter'].sudo().set_param('pos_aplazame.aplazame_sandbox_mode', self.aplazame_sandbox_mode)

        super(ResConfigSettings, self).set_values()
