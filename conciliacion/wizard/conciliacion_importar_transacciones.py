# -*- coding: utf-8 -*-

import logging
import tempfile
import binascii
import xlrd
import base64
import csv
import io

from datetime import datetime
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _

_logger = logging.getLogger(__name__)


class ImportarTransacciones(models.Model):
    _name = "conciliacion.importar_transacciones"
    _description = "Importar transacciones"
    
    bank_statement_id = fields.Many2one("account.bank.statement", string="Extracto")
    fichero = fields.Binary('Fichero')
    
    def action_importar(self):
        decrypted = base64.b64decode(self.fichero).decode('utf-8')
        with io.StringIO(decrypted) as fp:
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            for row in reader:
                neto = 0
                comisiones = 0
                transferencias_banco = 0
                recordlist = record_data.split(u'\n')
                for line in recordlist:
                    if not line:
                        pass

                    try:  debit = float(line[10])
                    except: debit = 0

                    try:  credit = float(line[11])
                    except: credit = 0

                    neto += credit - debit

                    try:  markup = float(line[17])
                    except: markup = 0

                    try:  scheme_fees = float(line[18])
                    except: scheme_fees = 0

                    comisiones += markup + scheme_fees

                    try:  interchange = float(line[19])
                    except: interchange = 0

                    transferencias_banco += interchange

                self.env['account.bank.statement.line'].create({
                    'payment_ref': "Neto",
                    'statement_id': self.bank_statement_id.id,
                    'amount': neto
                })
                
                self.env['account.bank.statement.line'].create({
                    'payment_ref': "Comisiones",
                    'statement_id': self.bank_statement_id.id,
                    'amount': comisiones
                })
                
                self.env['account.bank.statement.line'].create({
                    'payment_ref': "Transferencias a bancos",
                    'statement_id': self.bank_statement_id.id,
                    'amount': transferencias_banco
                })
        
        
    def open_wizard(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }