# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockPicking(models.Model):
    _inherit = "stock.picking"

    number_of_packages = fields.Integer(
        string="Number of Packages",
        compute="_compute_number_of_packages",
        readonly=False,
        store=True,
    )

    @api.depends("package_ids")
    def _compute_number_of_packages(self):
        for picking in self:
            picking.number_of_packages = len(picking.package_ids) or 1

    def _check_immediate(self):
        immediate_pickings = self.browse()
        #precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        #for picking in self:
        #    if all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel'))):
        #        immediate_pickings |= picking
        #return immediate_pickings

        for picking in self:
            if picking['carrier_id'].id == 12 and picking.picking_type_id.id == 5:
                immediate_pickings |= picking
            else:
                immediate_pickings = super(StockPicking, self)._check_immediate()

        return immediate_pickings