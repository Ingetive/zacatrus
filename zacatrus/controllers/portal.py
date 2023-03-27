# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.account.controllers.portal import PortalAccount


class PortalAccountZacatrus(PortalAccount):
    def _get_invoices_domain(self):
        return [
            ('state', 'not in', ('cancel', 'draft')), 
            ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt'))
        ]

    
