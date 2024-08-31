import logging
from odoo import models

_logger = logging.getLogger(__name__)

class Zconta(models.Model):
    _name = 'zacatrus.zconta'
    _description = 'Zacatrus helper conta methods'

    def createStatementFromApi(self, statementData, statementId, name, webBankJournal = 59):
        args = [
            ('payment_ref', '=', statementData['order_id']),
            ('amount', '=', statementData['amount'])
        ]
        existingLines = self.env['account.bank.statement.line'].search_read(args)
        for existingLine in existingLines:
            if existingLine['statement_id']:
                args = [
                    ('id', '=', existingLine['statement_id'][0]),
                    ('journal_id', '=', webBankJournal)
                ]
                existingStatements = self.env['account.bank.statement'].search(args)
                for statement in existingStatements:
                    return statement.id
            else:
                return False

        if not statementId:
            data = {
                'journal_id': webBankJournal,
                'name': name
            }
            statementId = self.env['account.bank.statement'].create(data)
        
        args = [
            ("id", "=", statementId)
        ]
        statements = self.env['account.bank.statement'].search( args )
        for statement in statements:
            statement.write({ 'balance_end_real': statement['balance_start'] + statementData['amount'] })

        description = f"{statementData['order_id']}"
        line = {
            'statement_id': statementId, 
            'payment_ref': description, 'amount': statementData['amount'], 
            'journal_id': webBankJournal, 
        }
        if 'date' in statementData:
            line['date'] = statementData['date']

        self.env['account.bank.statement.line'].create(line)

        return statementId

    def balanceRecalc(self, statementId):
        if statementId:
            statements = self.env['account.bank.statement'].search([('id', '=', statementId)])
            for statement in statements:
                balanceStart = statement.balance_start
                if balanceStart == 0:
                    pargs = [('journal_id', '=', statement.journal_id[0])]
                    pfields = ['name', 'balance_start', 'balance_end_real']
                    prevs = self.env['account.bank.statement'].search_read(pargs, pfields, 1, 1, 'id DESC')
                    for prev in prevs:
                        if fix:
                            data = {
                                'balance_start': prev['balance_end_real']
                            }
                            statement.write(data)
                            balanceStart = prev['balance_end_real']
                largs = [('statement_id', '=', statementId)]
                lines = self.env['account.bank.statement.line'].search_read(largs)
                total = 0 
                for line in lines:
                    total += line['amount']
                if not balanceStart+total == statement.balance_end_real:
                    statement.write( {'balance_end_real': balanceStart+total} )
            