# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
    nombre_fichero = fields.Char("Nombre fichero importado")
    neto_importado = fields.Monetary("Neto importado")
    
    def action_importar_transacciones(self):
        return self.env["conciliacion.importar_transacciones"].create({"bank_statement_id": self.id}).open_wizard()