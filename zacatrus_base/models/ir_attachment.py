# -*- coding: utf-8 -*-

import base64, json
import requests
from odoo import models, fields, api


class Attachment(models.Model):
    _inherit = 'ir.attachment'    
    
    def remotePrint(self, record):
        if record.res_model == 'stock.picking':
            printnodeKey = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.printnode_key')
            printerId = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.dhl_segovia_printer_id')
            if printnodeKey and printerId:
                pickings = self.env['stock_picking'].sudo().search_read([
                    ('id', '=', record.res_id)
                ], ['carrier_id'])

                for picking in pickings:
                    if picking.carrier_id == 12:
                        data = {
                          "content": record.datas ,
                          "printerId": int(printerId),
                          "contentType": "raw_base64",
                          "title": record.res_name
                        }
                        requests.post(
                            "https://api.printnode.com/printjobs", auth=(printnodeKey, ""),
                            json=data
                        )