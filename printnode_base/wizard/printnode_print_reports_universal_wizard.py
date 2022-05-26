# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import exceptions, fields, models, api, _


REPORT_DOMAIN = [
    ('report_type', 'in', ['qweb-pdf', 'qweb-text', 'py3o']),
    ('report_name', '!=', 'sale.report_saleorder_pro_forma'),
    ('report_name', '!=', 'product.report_pricelist'),
]


class PrintnodePrintReportsUniversalWizard(models.TransientModel):
    _name = 'printnode.print.reports.universal.wizard'
    _inherit = 'printnode.report.abstract.wizard'
    _description = 'Print Reports Wizard'

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        domain=lambda self: self._get_available_reports()
    )
    record_names = fields.Text(
        string='Will be printed',
        readonly=True,
        default=lambda self: self._get_record_names(),
    )

    def _default_printer_id(self):
        """
        Return default printer for wizard
        """
        # There can be default report from settings (this method called before the deafult value
        # to report_id will be applied)
        report_id = self.report_id or self.env.company.def_wizard_report_id

        # User rules
        user_rules_printer_id = self.env['printnode.rule'].search([
            ('user_id', '=', self.env.uid),
            ('report_id', '=', report_id.id),  # There will be no rules for report_id = False
        ], limit=1).printer_id

        # Workstation printer
        workstation_printer_id = self.env.user._get_workstation_device(
            'printnode_workstation_printer_id')

        # Priority:
        # 1. Printer from User Rules (if exists)
        # 2. Default Workstation Printer (User preferences)
        # 3. Default printer for current user (User Preferences)
        # 4. Default printer for current company (Settings)
        return user_rules_printer_id or workstation_printer_id or \
            self.env.user.printnode_printer or self.env.company.printnode_printer

    @api.constrains('number_copy')
    def _check_quantity(self):
        for rec in self:
            if rec.number_copy < 1:
                raise exceptions.ValidationError(
                    _('Quantity can not be less than 1')
                )

    @api.onchange('report_id')
    def _change_wizard_printer(self):
        self.printer_id = self._default_printer_id()

    def get_report(self):
        self.ensure_one()
        return self.report_id

    def get_docids(self):
        self.ensure_one()
        objects = self._get_records()
        return objects

    def _get_records(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if not (active_ids and active_model):
            return
        return self.env[active_model].browse(active_ids)

    def _get_record_names(self):
        records = self._get_records()

        if records:
            return ", ".join([rec.display_name for rec in records])

        return ''

    def _get_available_reports(self):
        active_model = self.env.context.get('active_model')
        return [*REPORT_DOMAIN, ('model', '=', active_model)]
