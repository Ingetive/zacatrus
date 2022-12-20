# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def __get_bank_statements_available_sources(self):
        res = super(AccountJournal, self).__get_bank_statements_available_sources()
        res.append(("adyen", "Adyen (CSV)"))
        return res