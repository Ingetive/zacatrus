# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    last_order = fields.Integer(readonly=False)
    fichas_product_id = fields.Many2one(
        'product.product', 
        string="Fichas Product",
        default_model='zacasocios.fichas_product_id'  # Almacena el valor en ir.config_parameter
    )
    block_magento_sync = fields.Boolean(readonly=False, string="Bloquear procesamiento con Magento", help="Evita procesar la cola.")


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        fichas_product_id = self.env['ir.config_parameter'].sudo().get_param('zacasocios.fichas_product_id', default=0)
 
        res.update(
            last_order = self.env['ir.config_parameter'].sudo().get_param('zacasocios.last_order'),
            fichas_product_id = int(fichas_product_id) if fichas_product_id else False,
            block_magento_sync = self.env['ir.config_parameter'].sudo().get_param('zacasocios.block_magento_sync')
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('zacasocios.last_order', self.last_order)
        self.env['ir.config_parameter'].sudo().set_param('zacasocios.block_magento_sync', self.block_magento_sync)

        if self.fichas_product_id:
            self.env['ir.config_parameter'].sudo().set_param('zacasocios.fichas_product_id', self.fichas_product_id.id)
        else:
            self.env['ir.config_parameter'].sudo().set_param('zacasocios.fichas_product_id', False)
        

        super(ResConfigSettings, self).set_values()
