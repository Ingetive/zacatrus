# -*- coding: utf-8 -*-

import base64, json
import requests
from odoo import models, fields, api


class Attachment(models.Model):
    _inherit = 'ir.attachment'    
    
    def remotePrint(self, record):
        printerId = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.dhl_segovia_printer_id')
        if printerId:
            data = {
              "content": record.datas ,
              "printerId": int(printerId),
              "contentType": "raw_base64",
              "title": record.res_name
            }

            try:
                if data:
                    response = requests.post(
                      "https://api.printnode.com/printjobs", 
                      auth=("fHfEHpfLEhwzppEbDH6zbTHamDI6WciYbRxjQZqpRF8", ""), json=data
                    )

                #info = response.json()
            except Exception as e:
              raise e