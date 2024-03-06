# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    x_partner_id8 = fields.Char("Id. en Odoo 8")
    
    @api.onchange("country_id")
    def _onchange_country(self):
        """ Overwrite base/models/res_partner.py
        """
        if self.country_id.code == "FR":
            self.fiscal_position_type = "b2c"
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.actualizar_tipo_pos_fical()
        return res
    
    def write(self, vals):
        res = super().write(vals)
        
        if "country_id" in vals:
            self.actualizar_tipo_pos_fical()
        return res
    
    def actualizar_tipo_pos_fical(self):
        for r in self:
            if r.country_id.code == "FR":
                r.fiscal_position_type = "b2c"
