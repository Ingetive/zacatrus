import logging

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def dhl_parcel_send_shipping(self, pickings):
        _logger.debug(f"Zacalog: dhl_parcel_send_shipping")

        for picking in pickings:
        if picking.carrier_id == 13 and picking.number_of_packages > 1:
            picking.write({
                'carrier_id' : newCarrierId
            })
            _logger.debug(f"Zacalog: dhl_parcel_send_shipping modificado {picking['name']}")


        super().dhl_parcel_send_shipping(pickings)