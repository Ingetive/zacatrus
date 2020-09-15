# -*- coding: utf-8 -*-
# © 2018 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_pinpad_via_proxy = fields.Boolean("Connect to verifone Pinpad")
    pinpad_port = fields.Char("PinPad Port")
    pinpad_customer = fields.Char("PinPad Customer")
    pinpad_shop = fields.Char("PinPad Shop")
    pinpad_pos = fields.Char("PinPad POS")
    pinpad_host = fields.Char("PinPad HOST")
