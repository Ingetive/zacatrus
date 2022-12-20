# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
    neto_importado = fields.Monetary("Neto importado")