# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ftpserver = fields.Char(string='localhost', readonly=False)
    ftpuser = fields.Char(readonly=False)
    ftppassword = fields.Char(readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res.update(
            ftpserver = self.env['ir.config_parameter'].sudo().get_param('zacaedi.ftpserver'),
            ftpuser = self.env['ir.config_parameter'].sudo().get_param('zacaedi.ftpuser'),
            ftppassword = self.env['ir.config_parameter'].sudo().get_param('zacaedi.ftppassword'),
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.ftpserver', self.ftpserver)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.ftpuser', self.ftpuser)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.ftppassword', self.ftppassword)

        super(ResConfigSettings, self).set_values()
