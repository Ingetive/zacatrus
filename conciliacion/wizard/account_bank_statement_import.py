# -*- coding: utf-8 -*-
import logging
import tempfile
import binascii
import xlrd
import base64
import csv
import io

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'
    
    def _default_journal(self):
        return self.env.context.get("journal_id", None)
    
    fichero_adyen = fields.Binary('Fichero Adyen')
    journal_id = fields.Many2one("account.journal", default=_default_journal)
    journal_bank_statements_source = fields.Selection(related="journal_id.bank_statements_source")
    
    def import_file(self):
        if self.journal_id.bank_statements_source == "adyen":
            return self.action_importar_adyen()
        return super().import_file()
        
    def action_importar_adyen(self):
        AccountMove = self.env['account.move']
        decrypted = base64.b64decode(self.fichero_adyen).decode('utf-8')
        with io.StringIO(decrypted) as fp:
            sequence = 0

            line_values =[]
            lineas_extracto = {}
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            for line in reader:
                neto = 0
                comisiones_venta = 0
                comisiones_transferencia = 0
                transferencia = 0
                name = line[1]
                if name == 'Merchant Account': #Saltamos cabecera
                    continue
                if name not in ['ZacatrusPOS', 'ZacatrusEs']:
                    raise ValidationError("El fichero no es válido.")
                if not line or len(line) < 8:
                    continue
                fecha = self._convert_to_date(line[5])
                if line[7] == "Fee":
                    comisiones_transferencia = self._convert_to_float(line[14])
                elif line[7] == "MerchantPayout":
                    transferencia = self._convert_to_float(line[14])
                elif line[7] in ["Settled", "Refunded"]:
                    debit = self._convert_to_float(line[10])
                    credit = self._convert_to_float(line[11])
                    neto = credit - debit
                    
                    commission = self._convert_to_float(line[16])
                    markup = self._convert_to_float(line[17])
                    scheme_fees = self._convert_to_float(line[18])
                    interchange = self._convert_to_float(line[19])
                    comisiones_venta += interchange + markup + scheme_fees + commission

                if fecha in lineas_extracto:
                    lineas_extracto[fecha]['neto'] += neto
                    lineas_extracto[fecha]['comisiones_venta'] += comisiones_venta
                    lineas_extracto[fecha]['comisiones_transferencia'] += comisiones_transferencia
                    lineas_extracto[fecha]['transferencia'] += transferencia
                else:
                    lineas_extracto[fecha] = {
                        'sequence': sequence,
                        'name' : name,
                        'neto' : neto,
                        'comisiones_venta' : comisiones_venta,
                        'comisiones_transferencia' : comisiones_transferencia,
                        'transferencia' :  transferencia,
                    }

            sequence = 0
            for fecha, resumen in lineas_extracto.items():
                amls_total = 0
                if resumen['name'] == 'ZacatrusPOS' and resumen['neto'] != 0:
                    amls = self.env['account.move.line'].search([
                        ('account_id', '=', self.env.ref("l10n_es.1_account_common_4300").id),
                        ('date', '=', fecha),
                        ('ref', '=ilike', f"POS/{fecha.strftime('%Y/%m/%d')}/%"),
                        ('name', 'ilike', "Adyen")
                    ])
                    
                    for aml in amls:
                        payment_ref = f"{aml.move_id.name}: {aml.name} : {aml.ref}"
                        amount = aml.debit or (aml.credit * -1)
                        line_values.append((0, 0, {
                            'sequence': sequence,
                            'date' : fecha,
                            'payment_ref': payment_ref,
                            'amount': amount
                        }))
                        amls_total += amount
                        sequence += 1
                    diferencia = resumen['neto'] - amls_total
                    if diferencia:
                        #Ha existido alguna devoución
                        line_values.append((0, 0, {
                            'sequence': sequence,
                            'date' : fecha,
                            'payment_ref': "Diferencia (Devoluciones)",
                            'amount': diferencia,
                        }))
                        sequence += 1

                if resumen['name'] == "ZacatrusEs":
                    if resumen['neto']:
                        line_values.append((0, 0, {
                            'sequence': sequence,
                            'date' : fecha,
                            'payment_ref': 'Ventas',
                            'amount': resumen['neto']
                        }))
                        sequence += 1

                if resumen['comisiones_venta']:
                    line_values.extend([(0, 0, {
                            'sequence': sequence + 1,
                            'date' : fecha,
                            'payment_ref': "Comisiones venta",
                            'amount': resumen['comisiones_venta'] * -1
                        })])
                    sequence += 1

                if resumen['comisiones_transferencia']:
                    line_values.extend([(0, 0, {
                            'sequence': sequence + 1,
                            'date' : fecha,
                            'payment_ref': "Comisiones transferencia",
                            'amount': resumen['comisiones_transferencia'] * -1
                        })])
                if resumen['transferencia']:
                    line_values.extend([(0, 0, {
                            'sequence': sequence + 1,
                            'date' : fecha,
                            'payment_ref': "Transferencia",
                            'amount': resumen['transferencia'] * -1
                        })])
                    sequence += 1

            if fecha:
                name_statement = f"{name} {fecha.strftime('%d/%m/%Y')}"
            
            bank_statement = self.env['account.bank.statement'].create({
                'name': name_statement,
                'journal_id': self.journal_id.id,
                'date': fecha.strftime('%Y-%m-%d') if fecha else fields.Date.today(),
                'neto_importado': neto,
                "line_ids": line_values
            })

            if bank_statement.balance_end == 0 and (
                (name == 'ZacatrusPOS' and round(neto, 2) == round(amls_total, 2)) or
                (name == 'ZacatrusEs' and bank_statement.line_ids)
            ):
                bank_statement.button_post()
                
            action = self.env['ir.actions.act_window']._for_xml_id('account.action_bank_statement_tree')
            form = self.env.ref('account.view_bank_statement_form', False)
            action['views'] = [(form.id if form else False, 'form')]
            action['res_id'] = bank_statement.id
            return action

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
        