import logging
from odoo import http
_logger = logging.getLogger(__name__)

class PaylandsController(http.Controller):
    @http.route('/payment/paylands/return', auth='public', type="json")
    def handler(self):
        #TODO: check ip is in whitelist
        res = http.request.jsonrequest
        print(res)
        _logger.warning("Zacalog: Paylands return :"+ str(res))
        payments = http.request.env["pos_paylands.payment"].search_read(domain=[])

        #buList = '<ul>'
        #for payment in payments:
        #    buList += f"<li>{payment['order_id']}</li>"
        #buList += '</ul>'

        return {"msg": "tal"}#f"<h1>Hello controller</h1> {buList}"#{"msg": "tal"}