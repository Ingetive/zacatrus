import re
import json
import requests
import string
import random
import sys
import logging
import hmac, base64, struct, hashlib, time, os

_logger = logging.getLogger(__name__)

from odoo import models, fields, api

class Card(models.Model):
    _name = 'pos_tarjezaca.card'
    _description = 'Tarjezaca'

    serial = fields.Char()
    code = fields.Char()

class Operation(models.Model):
    _name = 'pos_tarjezaca.operation'
    _description = 'Tarjezacas activadas'

    serial = fields.Char()
    valid = fields.Boolean()
    giftcard_id = fields.Char()
    cause = fields.Char()

class Connector(models.Model):
    _name = 'pos_tarjezaca.connector'
    _description = 'Tarjezaca Connector'

    def activateSoldCards(self):
        cardProductId = int(self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.card_product_id'))

        if not cardProductId:
            _logger.warning("Zacalog: Tarjezaca not configured.")
            return False


        prevLastOrder = int(self.env['ir.config_parameter'].sudo().get_param('pos_tarjezaca.pt_last_order'))
        if not prevLastOrder:
            _logger.warning("Zacalog: TarjezacaConnector not configured. Please, create TarjezacaConnector.pt_last_order")
            return False

        iargs = [
            ('product_id', '=', int(cardProductId)), 
            ('id', '>', prevLastOrder)
        ]
        posOrdersItems = self.env['pos.order.line'].search_read(iargs, limit=12)

        for posOrdersItem in posOrdersItems:
            lots = self.env['pos.pack.operation.lot'].search_read([('id', 'in', posOrdersItem['pack_lot_ids'])])
            for lot in lots:
                ops = self.env['pos_tarjezaca.operation'].search_count([("serial", '=', lot["lot_name"])])
                if ops > 0:
                    self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.pt_last_order', posOrdersItem["id"])
                    _logger.warning("Card "+lot["lot_name"]+" already processed")
                else:
                    posOrders = self.env['pos.order'].search_read([('id', '=', posOrdersItem["order_id"][0])])
                    valid = False
                    for posOrder in posOrders:
                        if posOrder["state"] in ["done", "paid", "invoiced"]:
                            valid = True

                    if valid:
                        cards = self.env['pos_tarjezaca.card'].search_count([("serial", '=', lot["lot_name"])])
                        if cards != 1:
                            cause = "Unknown."
                            if cards == 0:
                                cause = "Invalid serial."
                            if cards > 1:
                                cause = "Duplicated serial."
                            _logger.warning(f"Zacalog: Invalid serial for {lot['lot_name']}: {cause}")
                                
                            self.env['pos_tarjezaca.operation'].create({
                                'serial': lot["lot_name"], 'valid': False, 'cause': cause
                            })
                            self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.pt_last_order', posOrdersItem["id"])
                        else:
                            cards = self.env['pos_tarjezaca.card'].search_read([("serial", '=', lot["lot_name"])])
                            for card in cards:
                                _logger.info(f"Zacalog: Activating card {lot['lot_name']} with {str(posOrdersItem['price_unit'])} € (order {str(posOrdersItem['order_id'])})")
                                mCard = self.env['zacatrus.connector'].getGiftCardByCode(card["code"])
                                if mCard['total_count'] == 0:
                                    data = {
                                        "pattern": card["code"],
                                        "init_balance": posOrdersItem["price_unit"],
                                        "balance": posOrdersItem["price_unit"],
                                        "status": "1",
                                        "can_redeem": "1",
                                        "store_id": "1",
                                    }
                                    ret = self.env['zacatrus.connector'].createGiftCard(data)
                                    if 'giftcard_id' in ret:
                                        self.env['pos_tarjezaca.operation'].create({
                                            'serial': lot["lot_name"], 'valid': True, 'giftcard_id': ret["giftcard_id"]
                                        })
                                        self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.pt_last_order', posOrdersItem["id"])
                                    else:
                                        _logger.warning("Zacalog: Unable to generate code.")
                                else:
                                    self.env['pos_tarjezaca.operation'].create({
                                        'serial': lot["lot_name"], 'valid': False, 'cause': "Duplicated code."
                                    })
                                    self.env['ir.config_parameter'].sudo().set_param('pos_tarjezaca.pt_last_order', posOrdersItem["id"])
                                    _logger.warning("Zacalog: Code already exists.")
