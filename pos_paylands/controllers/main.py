import logging
from odoo import http
import hmac, base64, struct, hashlib, time, os
import json
_logger = logging.getLogger(__name__)

class PaylandsController(http.Controller):
    @http.route('/payment/paylands/return', auth='public', type="json")
    def handler(self):
        notification = http.request.jsonrequest

        #TODO: remove: for tests only
#        notification = {
#            'order': {
#                'uuid': '01AFF441-2D14-446F-94EA-4C057B734DC3', 'created': '2023-04-04T15:41:24+0200', 'created_from_client_timezone': '2023-04-04T15:41:24+0200', 'amount': 5000, 'currency': '978', 'paid': True, 'status': 'SUCCESS', 'safe': True, 'refunded': 0, 'additional': 'Additional info', 'service': 'CREDORAX', 'service_uuid': '4EC9FDC5-35FD-4F7A-AD69-184329543A48', 'customer': '12345678Z', 'cof_txnid': None, 
#                'transactions': [
#                    {
#                        'uuid': 'EFE87A32-2962-4D9B-9EC7-37E78B5D8362', 'created': '2023-04-04T15:41:24+0200', 'created_from_client_timezone': '2023-04-04T15:41:24+0200', 'operative': 'AUTHORIZATION', 'amount': 5000, 'authorization': '100000', 'processor_id': None, 
#                        'status': 'SUCCESS', 
#                        'error': 'NONE', 'source': None, 'antifraud': None, 'device': None, 'error_details': None, 
#                        'pos': {
#                            'requestor_id': 'API', 'pos_device_id': '642bd4e4841e297c4f8c0366', 
#                            'reversal': False, 'brand': 'MASTERCARD', 
#                            'masked_pan': '554001******0000', 'verification_method': 'NO', 
#                            'entry_mode': 'CLESS', 'expiry_date': None
#                        }
#                    }
#                ], 
#                'token': None, 'ip': None, 
#                'reference': 'POS3_Orden-09779-001-0001', 
#                'dynamic_descriptor': None, 'threeds_data': None
#            }, 
#            'client': {
#                'uuid': 'D329BC3B-0AE1-422E-9BB2-BCA1278487EE'
#            }, 
#            'validation_hash': 'aa06c5980f565b44ceae158044dc486c49067285a7d2401263ad807ceb0bd6f3'
#        }

        #cancelacion:
        #notification = {'order': {'uuid': '404C0CC3-4A3F-47F4-AEF1-4D56471299AC', 'created': '2023-04-05T17:57:18+0200', 'created_from_client_timezone': '2023-04-05T17:57:18+0200', 'amount': 5000, 'currency': '978', 'paid': False, 'status': 'CANCELLED', 'safe': True, 'refunded': 0, 'additional': 'Additional info', 'service': 'CREDORAX', 'service_uuid': '435A61DC-BC1A-45E2-921C-17BC5BA47687', 'customer': '12345678Z', 'cof_txnid': None, 'transactions': [{'uuid': 'F9AF2321-E755-4BC5-98C7-4797DFA42646', 'created': '2023-04-05T17:57:18+0200', 'created_from_client_timezone': '2023-04-05T17:57:18+0200', 'operative': 'AUTHORIZATION', 'amount': 5000, 'authorization': '', 'processor_id': None, 'status': 'CANCELLED', 'error': 'NONE', 'source': None, 'antifraud': None, 'device': None, 'error_details': None, 'pos': {'requestor_id': 'API', 'pos_device_id': '641d793e4512905387c04410', 'reversal': False, 'brand': None, 'masked_pan': None, 'verification_method': '', 'entry_mode': None, 'expiry_date': None}}], 'token': None, 'ip': None, 'reference': 'POS3_Orden-09779-002-0005', 'dynamic_descriptor': None, 'threeds_data': None}, 'client': {'uuid': 'D329BC3B-0AE1-422E-9BB2-BCA1278487EE'}, 'validation_hash': '1d2939a29129d5933d92d483eed14a54ee9f38050ca7c075d77aa9a1747a636b'}

        print(notification)
        _logger.info("Zacalog: Paylands return :"+ str(notification))

        # Check hash
        signature = http.request.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_signature')
        array = {}
        array['order'] = notification['order']
        array['client'] = notification['client']
        #array['extra_data'] = None
        data = json.dumps(array, separators=(",", ":"))
        validationHash = hashlib.sha256((data + signature).encode())
        if validationHash.hexdigest() != notification['validation_hash']:
            raise Exception("Sorry, validation failed") 

        #TODO: remove
        #notification['order']['reference'] = 'POS1_Order-00001-059-0001'

        ok = False
        status = -1
        if notification['order']['status'] == 'REFUSED':
            args = [
                ('order_id', '=', notification['order']['reference'])
            ]
            payments = http.request.env["pos_paylands.payment"].search(args)
            for payment in payments:
                payment.write({'status': 500})
                status = 500
        if notification['order']['status'] == 'CANCELLED':
            args = [
                ('order_id', '=', notification['order']['reference'])
            ]
            payments = http.request.env["pos_paylands.payment"].search(args)
            for payment in payments:
                payment.write({'status': 300})
                status = 300
        elif notification['order']['status'] == 'SUCCESS':
            for transaction in notification['order']['transactions']:
                if transaction['status'] == 'SUCCESS':
                    ok = True
                else:
                    ok = False
                    break
            if ok:
                args = [
                    ('order_id', '=', notification['order']['reference'])
                ]
                payments = http.request.env["pos_paylands.payment"].search(args)
                for payment in payments:
                    print(f"<li>{payment['order_id']} {payment['status']}</li>")
                    print(payment)
                    status = 200
                    payment.write({'status': 200})

        return {"ok": ok, "status": status}