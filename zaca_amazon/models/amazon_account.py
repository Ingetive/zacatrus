from odoo import _, api, exceptions, fields, models
import logging

_logger = logging.getLogger(__name__)


class AmazonAccount(models.Model):
    _inherit = 'amazon.account'

    fba_location_id = fields.Many2one(
        string="Stock Location for FBA",
        help="The location of the stock managed by Amazon under the Amazon Fulfillment program.",
        comodel_name='stock.location',
        domain="[('usage', '=', 'internal'), ('company_id', '=', company_id)]",
        check_company=True,
    )

    def _create_order_from_data(self, order_data):
        order = super()._create_order_from_data(order_data)

        if self.fba_location_id.warehouse_id and order.amazon_channel == 'fba':
            vals = {
                'warehouse_id': self.fba_location_id.warehouse_id.id,
            }
            order.write(vals)

        return order