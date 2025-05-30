# -*- coding: utf-8 -*-

import logging, os
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ftpserver = fields.Char(string='localhost', readonly=False)
    ftpuser = fields.Char(readonly=False)
    ftppassword = fields.Char(readonly=False)
    inputpath = fields.Char(readonly=False)
    outputpath = fields.Char(readonly=False)
    invoicesoutputpath = fields.Char(readonly=False)
    block_partner_ids = fields.Char(readonly=False)
    notify_user_ids = fields.Char(readonly=False)
    error_level = fields.Selection([
        ('30', 'Info'),
        ('20', 'Warning'),
        ('10', 'Error'),
    ], string="Nivel de error para notificaciones", default='30')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res.update(
            ftpserver = self.env['ir.config_parameter'].sudo().get_param('zacaedi.ftpserver'),
            ftpuser = self.env['ir.config_parameter'].sudo().get_param('zacaedi.ftpuser'),
            ftppassword = self.env['ir.config_parameter'].sudo().get_param('zacaedi.ftppassword'),
            inputpath = self.env['ir.config_parameter'].sudo().get_param('zacaedi.inputpath'),
            outputpath = self.env['ir.config_parameter'].sudo().get_param('zacaedi.outputpath'),
            invoicesoutputpath = self.env['ir.config_parameter'].sudo().get_param('zacaedi.invoicesoutputpath'),
            block_partner_ids = self.env['ir.config_parameter'].sudo().get_param('zacaedi.block_partner_ids'),
            notify_user_ids = self.env['ir.config_parameter'].sudo().get_param('zacaedi.notify_user_ids'),
            error_level=self.env['ir.config_parameter'].sudo().get_param('zacaedi.error_level', default='30')
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.ftpserver', self.ftpserver)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.ftpuser', self.ftpuser)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.ftppassword', self.ftppassword)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.inputpath', self.inputpath)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.outputpath', self.outputpath)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.invoicesoutputpath', self.invoicesoutputpath)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.block_partner_ids', self.block_partner_ids)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.notify_user_ids', self.notify_user_ids)
        self.env['ir.config_parameter'].sudo().set_param('zacaedi.error_level', self.error_level)

        super(ResConfigSettings, self).set_values()

    def getSeresFtpServer(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        ftpServer = self.env['ir.config_parameter'].sudo().get_param('zacaedi.ftpserver')
        if not odooEnv or odooEnv == 'staging':
            if ftpServer.find('[test]') == -1:
                _logger.error(f"Zacalog: odooEnv: {odooEnv}; ftpServer: {ftpServer}; [test] string not found in ftp server.")
            else:
                return ftpServer.replace("[test]", "")
        else:
            return ftpServer
            
        return False