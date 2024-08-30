import base64, os, logging
from datetime import datetime, timedelta
from odoo import models, fields

_logger = logging.getLogger(__name__)

EDI_BUNDLE_STATUS_INIT = 1
EDI_BUNDLE_STATUS_READY = 10
EDI_BUNDLE_STATUS_SENT = 20
EDI_BUNDLE_STATUS_INVOICED = 30

class Services(models.Model):
    _name = 'pos_paylands.service'
    _description = 'Servicios contratados con Paylands'

    code = fields.Char(string='code')
    name = fields.Char(string='name')
    sandbox = fields.Boolean()

    def getNameByCode(self, code):
        paylandsSandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_sandbox_mode')
        args = [
            ('code', '=', code),
            ('sandbox', '=', paylandsSandboxMode)
        ]
        services = self.search( args )
        for service in services:
            return service.name
        
        return code