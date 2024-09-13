# -*- coding: utf-8 -*-

import logging, os
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    magento_url = fields.Char(string='Ya sabes, http://...', readonly=False)
    magento_user = fields.Char(readonly=False)
    magento_password = fields.Char(readonly=False)
    magento_secret = fields.Char(readonly=False)

    magento_token = fields.Char(readonly=False)

    printnode_key = fields.Char(readonly=False)
    dhl_segovia_printer_id = fields.Char(readonly=False)
    dhl_distri_printer_id = fields.Char(readonly=False)
    card_product_id = fields.Many2one('product.product', string="Gift Card product", help="La tarjeta física que se vende en tienda.", readonly=False)
    fichas_product_id = fields.Many2one('product.product', string="Fichas product", help="El producto que se aplica al añadir fichas en el pos.", readonly=False)

    reconcile_one_month_only = fields.Boolean(readonly=False, string="Solo concilia un mes", help="Para evitar sobre cargas, solo reconcilia lo del primer mes a partir de la fecha indicada en el modelo.")

    block_partner_ids = fields.Char(readonly=False)
    notify_user_ids = fields.Char(readonly=False)
    error_level = fields.Selection([
        ('30', 'Info'),
        ('20', 'Warning'),
        ('10', 'Error'),
    ], string="Nivel de error para notificaciones", default='30')

    syncer_active = fields.Boolean()
    syncer_sync_active = fields.Boolean()
    slack_token = fields.Char()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        #_logger.warning("_TZ: card:"+(self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.fichas_product_id')))

        cardProductId = None
        fichasProductId = None
        if self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.card_product_id') and self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.card_product_id').isnumeric():
            cardProductId = int(self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.card_product_id'))
        if self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.fichas_product_id') and self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.fichas_product_id').isnumeric():
            fichasProductId = int(self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.fichas_product_id'))
        res.update(
            magento_url = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_url'),
            printnode_key = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.printnode_key'),
            dhl_segovia_printer_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.dhl_segovia_printer_id'),
            dhl_distri_printer_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.dhl_distri_printer_id'),
            magento_user = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_user'),
            card_product_id = cardProductId,
            fichas_product_id = fichasProductId,
            reconcile_one_month_only = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.reconcile_one_month_only'),
            #magento_password = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_password'),
            block_partner_ids = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.block_partner_ids'),
            notify_user_ids = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.notify_user_ids'),
            error_level=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.error_level', default='30'),
            magento_token=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_token'),
            
            syncer_active=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.syncer_active'),
            syncer_sync_active=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.syncer_sync_active'),

            slack_token=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.slack_token')
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.magento_url', self.magento_url)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.printnode_key', self.printnode_key)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.dhl_segovia_printer_id', self.dhl_segovia_printer_id)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.dhl_distri_printer_id', self.dhl_distri_printer_id)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.magento_user', self.magento_user)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.reconcile_one_month_only', self.reconcile_one_month_only)
        if self.card_product_id and self.card_product_id != "":
            _logger.warning("_TZ: card:"+str(self.card_product_id.id))
            self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.card_product_id', self.card_product_id.id)
        if self.fichas_product_id and self.fichas_product_id != "":
            _logger.warning("_TZ: fichas:"+str(self.fichas_product_id.id))
            self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.fichas_product_id', self.fichas_product_id.id)
        if self.magento_password and self.magento_password != "":
            self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.magento_password', self.magento_password)
        if self.magento_secret and self.magento_secret != "":
            self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.magento_secret', self.magento_secret)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.block_partner_ids', self.block_partner_ids)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.notify_user_ids', self.notify_user_ids)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.error_level', self.error_level)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.magento_token', self.magento_token)

        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.syncer_active', self.syncer_active)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.syncer_sync_active', self.syncer_sync_active)

        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.slack_token', self.slack_token)

        super(ResConfigSettings, self).set_values()

    def getSlackToken(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.slack_token')
        if not odooEnv or odooEnv == 'staging':
            if value.find('[test]') == -1:
                _logger.error(f"Zacalog: odooEnv: {odooEnv}; slack_token: {value}; [test] string not found in slack_token.")
            else:
                return value.replace("[test]", "")
        else:
            return value
            
        return False
    
    def getMagentoUrl(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.magento_url')
        if not odooEnv or odooEnv == 'staging':
            if value.find('[test]') == -1:
                _logger.error(f"Zacalog: odooEnv: {odooEnv}; getMagentoUrl: {value}; [test] string not found in MagentoUrl.")
            else:
                return value.replace("[test]", "")
        else:
            return value
            
        return False
    
    def getSyncerActive(self):
        return self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.syncer_active')

    def getSyncerSyncActive(self):
        return self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.syncer_sync_active')