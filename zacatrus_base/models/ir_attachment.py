# -*- coding: utf-8 -*-

import base64, json
import requests
from odoo import models, fields, api


class Attachment(models.Model):
    _inherit = 'ir.attachment'    
    
    def remotePrint(self, record = None):
        # TODO: Migración => Revisar con datos como funcionaria la acción automatizada y el cambio de printnode_base
        for attachment in self:
            if attachment.res_model == 'stock.picking':
                printnodeKey = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.printnode_key')
                printerId = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.dhl_segovia_printer_id')
                if printnodeKey and printerId:
                    pickings = self.env['stock.picking'].sudo().search_read([
                        ('id', '=', attachment.res_id)
                    ], ['carrier_id', 'picking_type_id'])

                    for picking in pickings:
                        # Es DHL y sale de Segovia
                        if picking['carrier_id'][0] == 14 and picking['picking_type_id'][0] == 5:
                            data = {
                              "content": attachment.datas ,
                              "printerId": int(printerId),
                              "contentType": "raw_base64",
                              "title": attachment.res_name
                            }
                            requests.post(
                                "https://api.printnode.com/printjobs", auth=(printnodeKey, ""),
                                json=data
                            )