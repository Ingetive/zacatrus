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
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class ImportarTransacciones(models.Model):
    _name = "conciliacion.importar_transacciones"
    _description = "Importar transacciones"
    
    bank_statement_id = fields.Many2one("account.bank.statement", string="Extracto")
    fichero = fields.Binary('Fichero')
    
    def action_importar(self):
        decrypted = base64.b64decode(self.fichero).decode('utf-8')
        with io.StringIO(decrypted) as fp:
            neto = 0
            comisiones_venta = 0
            comisiones_transferencia = 0
            transferencia = 0
            fecha = None
            
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            for line in reader:
                
                if not line or len(line) < 8:
                    continue
                elif line[7] == "Fee":
                    comisiones_transferencia = self._convert_to_float(line[14])
                elif line[7] == "MerchantPayout":
                    transferencia = self._convert_to_float(line[14])
                elif line[7] in ["Settled", "Refunded"]:
                    if not fecha:
                        fecha = self._convert_to_date(line[5])
                    debit = self._convert_to_float(line[10])
                    credit = self._convert_to_float(line[11])
                    neto += credit - debit

                    commission = self._convert_to_float(line[16])
                    markup = self._convert_to_float(line[17])
                    scheme_fees = self._convert_to_float(line[18])
                    interchange = self._convert_to_float(line[19])
                    comisiones_venta += interchange + markup + scheme_fees + commission
                
            sequence = 0
            if fecha:
                amls = self.env['account.move.line'].search([
                    # ('journal_id.id', '=', self.env.ref("point_of_sale.pos_sale_journal").id),
                    ('account_id', '=', self.env.ref("l10n_es.1_account_common_4300").id),
                    ('ref', '=ilike', f"POS/{fecha.strftime('%Y/%m/%d')}/%"),
                    ('name', 'ilike', "Adyen")
                ])
                
                for aml in amls:
                    payment_ref = f"{aml.move_id.name} : {aml.name} : {aml.ref}"
                    self.env['account.bank.statement.line'].create({
                        'sequence': sequence,
                        'payment_ref': payment_ref,
                        'statement_id': self.bank_statement_id.id,
                        'amount': aml.debit or (aml.credit * -1)
                    })
                    sequence += 1

            self.env['account.bank.statement.line'].create({
                'payment_ref': "Comisiones venta",
                'statement_id': self.bank_statement_id.id,
                'amount': comisiones_venta * -1
            })
            sequence += 1
            
            self.env['account.bank.statement.line'].create({
                'sequence': sequence,
                'payment_ref': "Comisiones transferencia",
                'statement_id': self.bank_statement_id.id,
                'amount': comisiones_transferencia * -1
            })
            sequence += 1
            
            self.env['account.bank.statement.line'].create({
                'sequence': sequence,
                'payment_ref': "Transferencia",
                'statement_id': self.bank_statement_id.id,
                'amount': transferencia * -1
            })

            self.bank_statement_id.write({
                'neto_importado': neto
            })
    
    @api.model
    def _convert_to_float(self, num_str):
        try:  
            return float(num_str)
        except:
            return 0.0
        
    @api.model
    def _convert_to_date(self, date_str):
        try:  
            return datetime.strptime(date_str, DATETIME_FORMAT).date()
        except:
            return None
        
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