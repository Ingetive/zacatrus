from odoo import _, api, exceptions, fields, models
import logging

_logger = logging.getLogger(__name__)


class AmazonAccount(models.Model):
    _inherit = 'amazon.account'

    def _process_order_data(self, order_data):
        """ Process the provided order data and return the matching sales order, if any.

        If no matching sales order is found, a new one is created if it is in a 'synchronizable'
        status: 'Shipped' or 'Unshipped', if it is respectively an FBA or an FBA order. If the
        matching sales order already exists and the Amazon order was canceled, the sales order is
        also canceled.

        Note: self.ensure_one()

        :param dict order_data: The order data to process.
        :return: The matching Amazon order, if any, as a `sale.order` record.
        :rtype: recordset of `sale.order`
        """
        self.ensure_one()

        # Search for the sales order based on its Amazon order reference.
        amazon_order_ref = order_data['AmazonOrderId']
        order = self.env['sale.order'].search(
            [('amazon_order_ref', '=', amazon_order_ref)], limit=1
        )
        amazon_status = order_data['OrderStatus']
        if not order:  # No sales order was found with the given Amazon order reference.
            fulfillment_channel = order_data['FulfillmentChannel']
            if amazon_status in const.STATUS_TO_SYNCHRONIZE[fulfillment_channel]:
                # Create the sales order and generate stock moves depending on the Amazon channel.
                order = self._create_order_from_data(order_data)
                if order.amazon_channel == 'fba':
                    self._generate_stock_moves(order)
                elif order.amazon_channel == 'fbm':
                    order.with_context(mail_notrack=True).action_done()
                _logger.info(
                    "Created a new sales order with amazon_order_ref %s for Amazon account with "
                    "id %s.", amazon_order_ref, self.id
                )
            else:
                _logger.info(
                    "Ignored Amazon order with reference %(ref)s and status %(status)s for Amazon "
                    "account with id %(account_id)s.",
                    {'ref': amazon_order_ref, 'status': amazon_status, 'account_id': self.id},
                )
        else:  # The sales order already exists.
            if amazon_status == 'Canceled' and order.state != 'cancel':
                order._action_cancel()
                _logger.info(
                    "Canceled sales order with amazon_order_ref %s for Amazon account with id %s.",
                    amazon_order_ref, self.id
                )
            else:
                _logger.info(
                    "Ignored already synchronized sales order with amazon_order_ref %s for Amazon"
                    "account with id %s.", amazon_order_ref, self.id
                )
        return order