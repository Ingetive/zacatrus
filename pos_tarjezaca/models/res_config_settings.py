# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pt_last_order = fields.Integer(readonly=False)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
 
        res.update(
            pt_last_order = self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.pt_last_order'),
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.pt_last_order', self.pt_last_order)

        super(ResConfigSettings, self).set_values()
