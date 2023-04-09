# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    paylands_sandbox_mode = fields.Boolean("Paylands en modo pruebas")
    paylands_signature = fields.Char("Firma digital")
    paylands_apikey = fields.Char("Api key")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        paylandsSandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_sandbox_mode')
        paylandsSignature = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_signature')
        paylandsApikey = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_apikey')
        res.update(
            paylands_sandbox_mode = paylandsSandboxMode,
            paylands_signature = paylandsSignature,
            paylands_apikey = paylandsApikey
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_sandbox_mode', self.paylands_sandbox_mode)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_signature', self.paylands_signature)
        self.env['ir.config_parameter'].sudo().set_param('pos_paylands.paylands_apikey', self.paylands_apikey)

        super(ResConfigSettings, self).set_values()
