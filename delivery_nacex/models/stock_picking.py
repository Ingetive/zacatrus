# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging
from odoo.http import request
import requests

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'
    
#     def open_website_url(self):
#         if self.carrier_id.delivery_type == "nacex":
#             response = requests.post("https://www.nacex.es/seguimientoFormulario.do", data={'envio': '99999'}, allow_redirects=True)
#             _logger.warning(response.url)
#             return request.redirect(response.url)
        
#         return super(Picking, self).open_website_url()