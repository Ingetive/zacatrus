# -*- coding: utf-8 -*-
# © 2018 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    verifone_operation = fields.Char('Verifone Operation', readonly=True)
    verifone_account = fields.Char('Verifone Account', readonly=True)
    verifone_card_number = fields.Char('Verifone Card Number', readonly=True)
    verifone_owner = fields.Char('Verifone Owner', readonly=True)
    verifone_store = fields.Char('Verifone Store', readonly=True)
    verifone_terminal = fields.Char('Verifone Terminal', readonly=True)
    verifone_operation_number = fields.Char('Verifone Operation Number',
                                            readonly=True)
    verifone_authorization_code = fields.Char('Verifone Authorization Code',
                                              readonly=True)
    verifone_aid = fields.Char('Verifone AID', readonly=True)
    verifone_lbl = fields.Char('Verifone LBL', readonly=True)
    verifone_bin = fields.Char('Verifone BIN', readonly=True)
    verifone_arc = fields.Char('Verifone ARC', readonly=True)
    verifone_reading_type = fields.Selection([
        ('1', 'Chip'),
        ('2', 'Magnetic Band'),
        ('3', 'Manual Input'),
        ('4', 'Contactless'),
        ('5', 'Mobile NFC')
    ], 'Verifone Reading Type', readonly=True)
    verifone_cvm = fields.Selection([
        ('1', 'PIN Operation, signature not necessary'),
        ('2', 'Contactless Operation, signature not necessary'),
        ('3', 'Signature Captured by the Pin-Pad'),
        ('4', 'Required Signature on ticket')
    ], 'Verifone CVM', readonly=True)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_bank_statement_line_payment_values(self, data):
        """Create a new payment for the order"""

        verifone = data.get('verifone_operation')
        payment_name = '%s - %s' % (self.name, self.pos_reference)
        if verifone:
            args = {
                'verifone_operation': data['verifone_operation'],
                'verifone_cvm': data['verifone_cvm'],
                'verifone_arc': data['verifone_arc'],
                'verifone_aid': data['verifone_aid'],
                'verifone_reading_type': data['verifone_reading_type'],
                'verifone_account': data['verifone_account'],
                'verifone_card_number': data['verifone_card_number'],
                'verifone_operation_number': data[
                    'verifone_operation_number'],
                'verifone_authorization_code': data[
                    'verifone_authorization_code'],
                'verifone_bin': data['verifone_bin'],
                'verifone_store': data['verifone_store'],
                'verifone_owner': data['verifone_owner'],
                'verifone_lbl': data['verifone_lbl'],
                'amount': data['amount'],
                'date': data.get('payment_date', fields.Date.context_today(
                    self)),
                'name': payment_name,
                'partner_id': self.env["res.partner"]._find_accounting_partner(
                    self.partner_id).id or False,
            }
        else:
            args = {
                'amount': data['amount'],
                'date': data.get('payment_date', fields.Date.context_today(
                    self)),
                'name': payment_name,
                'partner_id': self.env["res.partner"]._find_accounting_partner(
                    self.partner_id).id or False,
            }
        if data.get('payment_name'):
            payment_name += ': ' + data['payment_name']
        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id"

        journal = self.env['account.journal'].browse(journal_id)
        # use the company of the journal and not of the current user
        company_cxt = dict(
            self.env.context, force_company=journal.company_id.id)
        account_def = self.env['ir.property'].with_context(company_cxt).get(
            'property_account_receivable_id', 'res.partner')
        args['account_id'] = (
            self.partner_id.property_account_receivable_id.id) or (
            account_def and account_def.id) or False

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account'
                        'defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make'
                        'payment for the partner: "%s" (id:%d).') % (
                    self.partner_id.name, self.partner_id.id,)
            raise UserError(msg)

        context = dict(self.env.context)
        context.pop('pos_session_id', False)
        for statement in self.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break
        if not statement_id:
            raise UserError(_('You have to open at least one cashbox.'))

        args.update({
            'statement_id': statement_id,
            'pos_statement_id': self.id,
            'journal_id': journal_id,
            'ref': self.session_id.name,
        })

        return args

    def _payment_fields(self, ui_paymentline):
        verifone = ui_paymentline.get('verifone_operation')
        payment_date = ui_paymentline['name']
        payment_date = fields.Date.context_today(
            self, fields.Datetime.from_string(payment_date))
        if verifone:
            return {
                'amount': ui_paymentline['amount'] or 0.0,
                'payment_date': payment_date,
                'statement_id': ui_paymentline['statement_id'],
                'payment_name': ui_paymentline.get('note', False),
                'journal': ui_paymentline['journal_id'],
                'verifone_operation': ui_paymentline['verifone_operation'],
                'verifone_cvm': ui_paymentline['verifone_cvm'],
                'verifone_arc': ui_paymentline['verifone_arc'],
                'verifone_aid': ui_paymentline['verifone_aid'],
                'verifone_reading_type': ui_paymentline[
                    'verifone_reading_type'],
                'verifone_account': ui_paymentline['verifone_account'],
                'verifone_card_number': ui_paymentline['verifone_card_number'],
                'verifone_operation_number': ui_paymentline[
                    'verifone_operation_number'],
                'verifone_authorization_code': ui_paymentline[
                    'verifone_authorization_code'],
                'verifone_bin': ui_paymentline['verifone_bin'],
                'verifone_store': ui_paymentline['verifone_store'],
                'verifone_owner': ui_paymentline['verifone_owner'],
                'verifone_lbl': ui_paymentline['verifone_lbl'],
            }
        else:
            return {
                'amount': ui_paymentline['amount'] or 0.0,
                'payment_date': payment_date,
                'statement_id': ui_paymentline['statement_id'],
                'payment_name': ui_paymentline.get('note', False),
                'journal': ui_paymentline['journal_id'],
            }
