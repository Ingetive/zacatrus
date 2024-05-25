# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Account(models.Model):
    _inherit = 'account.account'
    
    @api.model
    def _search_new_account_code(self, company, digits, prefix):
        """ Overwrite account/models/account_account.py
        """
        for num in range(1, 10000):
            new_code = str(prefix.ljust(digits - len(str(num)), '0')) + str(num)
            rec = self.search([('code', '=', new_code), ('company_id', '=', company.id)], limit=1)
            if not rec:
                return new_code
        raise UserError(_('Cannot generate an unused account code.'))