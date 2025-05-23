from odoo import _, api, exceptions, fields, models
import logging
from odoo.addons.zaca_amazon import utils as amazon_utils

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
    
    def _sync_orders(self, auto_commit=True):
        self.sync_fba_inbound_shipments()

        return super()._sync_orders(auto_commit)

    def _assignShipment(self, _id, account):
        shipments = self.env['stock.picking'].search([
                ('picking_type_id', 'in', [115,122]),
                ('state', '=', 'assigned'),
                ('x_amz_shipping_id', '=', False),
                ('location_dest_id', '=', account.fba_location_id.id)
            ])
        count = 0
        for shipment in shipments:
            count += 1

        if count == 1:
            shipment.write({'x_amz_shipping_id': _id})
            _logger.info(f"Zacalog: Amazon shipment assigned {_id} {shipment.name}")


    def _generate_stock_moves(self, order):
        """ Generate a stock move for each product of the provided sales order.

        :param recordset order: The sales order to generate the stock moves for, as a `sale.order`
                                record.
        :return: The generated stock moves.
        :rtype: recordset of `stock.move`
        """
        customers_location = self.env.ref('stock.stock_location_customers')
        for order_line in order.order_line.filtered(
            lambda l: l.product_id.type != 'service' and not l.display_type
        ):
            stock_move = self.env['stock.move'].create({
                'name': _('Amazon move : %s', order.name),
                'company_id': self.company_id.id,
                'product_id': order_line.product_id.id,
                'product_uom_qty': order_line.product_uom_qty,
                'product_uom': order_line.product_uom.id,
                'location_id': self.fba_location_id.id,
                'location_dest_id': customers_location.id,
                'state': 'confirmed',
                'sale_line_id': order_line.id,
            })
            stock_move._action_assign()
            stock_move._set_quantity_done(order_line.product_uom_qty)
            stock_move._action_done()

    def sync_fba_inbound_shipments(self):
        accounts = self or self.search([])
        for account in accounts:
            account = account[0]  # Avoid pre-fetching after each cache invalidation.
            amazon_utils.ensure_account_is_set_up(account)
            last_updated_after = account.last_orders_sync 

            # Pull all recently updated orders and save the progress during synchronization.
            payload = {
                'LastUpdatedAfter': last_updated_after.isoformat(sep='T'),
                'MarketplaceIds': ','.join(account.active_marketplace_ids.mapped('api_ref')),
                'ShipmentStatusList': 'RECEIVING,SHIPPED,IN_TRANSIT,DELIVERED,CHECKED_IN',
            }
            
            try:
                # Pull the next batch of orders data.
                batch_data, has_next_page = amazon_utils.pull_batch_data(
                    account, 'getInboundShipments', payload                
                )
                orders_data = batch_data['ShipmentData']
                # Process the batch one order data at a time.
                for order_data in orders_data:
                    shipmentId = order_data['ShipmentId']
                    name = order_data['ShipmentName']
                    status = order_data['ShipmentStatus']
                    _logger.info(f"shipping {name} {shipmentId} is in status {status}")
                    if status not in ['DELIVERED','CHECKED_IN']:
                        pickings = self.env['stock.picking'].search([
                                ('x_amz_shipping_id', '=', shipmentId),
                            ])
                        exists = False
                        for picking in pickings:
                            exists = True
                            _logger.info(f"Zacalog: Amazon shipment exists {shipmentId} {picking.name}")
                        if not exists:
                            self._assignShipment(shipmentId, account)
                    if status in ['CHECKED_IN']:
                        shipments = self.env['stock.picking'].search([
                                ('x_amz_shipping_id', '=', shipmentId),
                            ])
                        for picking in shipments:
                            if picking.state != 'done':
                                for move in picking.move_ids:
                                    move.quantity_done = move.product_uom_qty
                                picking.button_validate()
                                _logger.info(f"Zacalog: Amazon shipment done {shipmentId} {picking.name}")
                                
            except amazon_utils.AmazonRateLimitError as error:
                _logger.info(
                    "Rate limit reached while synchronizing sales orders for Amazon account with "
                    "id %s. Operation: %s", account.id, error.operation
                )
                continue  # The remaining orders will be pulled later when the cron runs again.

