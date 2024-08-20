# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import markupsafe

from lxml import etree
from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.models import check_method_name
from odoo.addons.web.controllers.utils import clean_action
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang

_logger = logging.getLogger(__name__)


class BankRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    ##########################################################################################
    ### CORRERGIR ERROR DE CONCILIAR QUE TENIA EL MÓDULO DE LA ENTERPRISE ####################
    ### PROBAR MAS ADELANTE Y SI FUNCIONA SIN ESTA FUNCIÓN QUITARLA ##########################
    ##########################################################################################
    @api.depends('st_line_id')
    def _compute_line_ids(self):
        """ Convert the python dictionaries in 'lines_widget' to a bank.rec.edit.line recordset to ease the business
        computations.
        In case 'lines_widget' is empty, the default initial lines are generated.
        """
        for wizard in self:

            # The wizard already has lines.
            if wizard.line_ids:
                return

            # Protected fields by the orm like create_date should be excluded.
            protected_fields = set(models.MAGIC_COLUMNS + [self.CONCURRENCY_CHECK_FIELD])

            if wizard.lines_widget and wizard.lines_widget['lines']:
                # Create the `bank.rec.widget.line` from existing data in `lines_widget`.
                line_ids_commands = []
                for line_vals in wizard.lines_widget['lines']:
                    create_vals = {}
                    
                    for field_name, field in wizard.line_ids._fields.items():
                        if field_name in protected_fields:
                            continue
                        
                        value = line_vals[field_name]
                        if field.type == 'many2one':
                            create_vals[field_name] = value['id']
                        elif field.type in ['many2many', 'one2many']:
                            create_vals[field_name] = value['ids']
                        elif field.type == 'char':
                            create_vals[field_name] = value['value'] or ''
                        else:
                            create_vals[field_name] = value['value']

                    line_ids_commands.append(Command.create(create_vals))
                    
                wizard.line_ids = line_ids_commands
            else:
                # The wizard is opened for the first time. Create the default lines.
                line_ids_commands = [Command.clear(), Command.create(wizard._lines_widget_prepare_liquidity_line())]

                if wizard.st_line_id.is_reconciled:
                    # The statement line is already reconciled. We just need to preview the existing amls.
                    _liquidity_lines, _suspense_lines, other_lines = wizard.st_line_id._seek_for_lines()
                    for aml in other_lines:
                        exchange_diff_amls = (aml.matched_debit_ids + aml.matched_credit_ids) \
                            .exchange_move_id.line_ids.filtered(lambda l: l.account_id != aml.account_id)
                        if wizard.state == 'reconciled' and exchange_diff_amls:
                            line_ids_commands.append(
                                Command.create(wizard._lines_widget_prepare_aml_line(
                                    aml,  # Create the aml line with un-squashed amounts (aml - exchange diff)
                                    balance=aml.balance - sum(exchange_diff_amls.mapped('balance')),
                                    amount_currency=aml.amount_currency - sum(exchange_diff_amls.mapped('amount_currency')),
                                ))
                            )
                            for exchange_diff_aml in exchange_diff_amls:
                                line_ids_commands.append(
                                    Command.create(wizard._lines_widget_prepare_aml_line(exchange_diff_aml))
                                )
                        else:
                            line_ids_commands.append(Command.create(wizard._lines_widget_prepare_aml_line(aml)))
                wizard.line_ids = line_ids_commands

                wizard._lines_widget_add_auto_balance_line()
    
    @api.depends(
        'form_index',
        'state',
        'line_ids.account_id',
        'line_ids.date',
        'line_ids.name',
        'line_ids.partner_id',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.balance',
        'line_ids.analytic_distribution',
        'line_ids.tax_repartition_line_id',
        'line_ids.tax_ids',
        'line_ids.tax_tag_ids',
        'line_ids.group_tax_id',
        'line_ids.reconcile_model_id',
    )
    def _compute_lines_widget(self):
        """ Convert the bank.rec.widget.line recordset (line_ids fields) to a dictionary to fill the 'lines_widget'
        owl widget.
        """
        def format_distribution_name(display_name, percentage):
            precision = self.analytic_precision or 2

            if not float_compare(percentage, 100.00, precision):
                return display_name

            rounded_percentage = float_round(percentage, precision)
            rounded_percentage_without_trailing_zeros = str(rounded_percentage).rstrip('0').rstrip('.')

            return f"{display_name} {rounded_percentage_without_trailing_zeros}%"

        self._check_lines_widget_consistency()

        # Protected fields by the orm like create_date should be excluded.
        protected_fields = set(models.MAGIC_COLUMNS + [self.CONCURRENCY_CHECK_FIELD])

        for wizard in self:
            lines = wizard.line_ids

            # Sort the lines.
            sorted_lines = []
            auto_balance_lines = []
            epd_lines = []
            exchange_diff_map = {x.source_aml_id: x for x in lines.filtered(lambda x: x.flag == 'exchange_diff')}
            for line in lines:
                if line.flag == 'auto_balance':
                    auto_balance_lines.append(line)
                elif line.flag == 'early_payment':
                    epd_lines.append(line)
                elif line.flag != 'exchange_diff':
                    sorted_lines.append(line)
                    if line.flag == 'new_aml' and exchange_diff_map.get(line.source_aml_id):
                        sorted_lines.append(exchange_diff_map[line.source_aml_id])

            line_vals_list = []
            for line in sorted_lines + epd_lines + auto_balance_lines:
                js_vals = {}

                for field_name, field in line._fields.items():
                    if field_name in protected_fields:
                        continue
                    
                    value = line[field_name]
                    if field.type == 'date':
                        js_vals[field_name] = {
                            'display': tools.format_date(self.env, value),
                            'value': fields.Date.to_string(value),
                        }
                    elif field.type == 'char':
                        js_vals[field_name] = {'value': value or ''}
                    elif field.type == 'monetary':
                        currency = line[field.currency_field]
                        js_vals[field_name] = {
                            'display': formatLang(self.env, value, currency_obj=currency),
                            'value': value,
                            'is_zero': currency.is_zero(value),
                        }
                    elif field.type == 'many2one':
                        record = value._origin
                        js_vals[field_name] = {
                            'display': record.display_name or '',
                            'id': record.id,
                        }
                    elif field.type in ['many2many', 'one2many']: # Parte cambiadad para que no de error
                        records = value._origin
                        js_vals[field_name] = {
                            'display': records.mapped('display_name'),
                            'ids': records.ids,
                        }
                    elif field_name == 'analytic_distribution':
                        js_vals[field_name] = {'value': value}

                        if value:
                            analytic_account_ids = [int(analytic_account_id) for analytic_account_id in value]
                            analytic_accounts = self.env['account.analytic.account'].browse(analytic_account_ids).read(['id', 'display_name', 'color'])

                            js_vals[field_name]['display'] = [
                                {
                                    'id': analytic_account['id'],
                                    'text': format_distribution_name(analytic_account['display_name'], value.get(str(analytic_account['id']))),
                                    'colorIndex': analytic_account['color'],
                                } for analytic_account in analytic_accounts
                            ]
                    else:
                        js_vals[field_name] = {'value': value}
                line_vals_list.append(js_vals)

            extra_notes = []
            bank_account = wizard.st_line_id.partner_bank_id.display_name or wizard.st_line_id.account_number
            if bank_account:
                extra_notes.append(bank_account)

            bool_analytic_distribution = False
            for line in wizard.line_ids:
                if line.analytic_distribution:
                    bool_analytic_distribution = True
                    break

            wizard.lines_widget = {
                'lines': line_vals_list,

                'display_multi_currency_column': wizard.line_ids.currency_id != wizard.company_currency_id,
                'display_taxes_column': bool(wizard.line_ids.tax_ids),
                'display_analytic_distribution_column': bool_analytic_distribution,
                'form_index': wizard.form_index,
                'state': wizard.state,
                'partner_name': wizard.st_line_id.partner_name,
                'extra_notes': ' '.join(extra_notes) if extra_notes else None,
            }