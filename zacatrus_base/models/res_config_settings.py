# -*- coding: utf-8 -*-

import logging, os
from odoo import api, fields, models

_logger = logging.getLogger(__name__)   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    magento_url = fields.Char(string='URL de Magento', help='URL de l\'API Magento (ex: https://zacatrus.es/rest/all/V1/)', readonly=False)
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

    glovo_api_key = fields.Char()
    glovo_api_secret = fields.Char()
    
    last_sync_date = fields.Datetime(string='Dernière date de synchronisation', readonly=False, help='Date de la dernière synchronisation')
    
    # Champs modifiés avec des tables de relation spécifiques
    subscriber_pricelist_ids = fields.Many2many(
        'product.pricelist', 
        'zacatrus_subscriber_pricelist_rel',  # Nom spécifique de la table de relation
        'config_id',
        'pricelist_id',
        string='Listes de prix pour abonnés', 
        help='Listes de prix utilisées pour filtrer les nouveaux abonnés',
        readonly=False
    )
    subscriber_fiscal_position_ids = fields.Many2many(
        'account.fiscal.position',
        'zacatrus_subscriber_fiscal_position_rel',  # Nom spécifique de la table de relation
        'config_id',
        'fiscal_position_id',
        string='Positions fiscales pour abonnés',
        help='Positions fiscales utilisées pour filtrer les nouveaux abonnés',
        readonly=False
    )

    # Configuration Sendy
    sendy_url = fields.Char(string='URL Sendy', help='URL de votre installation Sendy', readonly=False)
    sendy_api_key = fields.Char(string='Clé API Sendy', help='Clé API pour l\'authentification Sendy', readonly=False)
    sendy_list_id = fields.Char(string='ID Liste Sendy', help='ID de la liste des abonnés dans Sendy', readonly=False)
    
    # Configuration équipe commerciale
    sales_team_id = fields.Many2one('crm.team', string='Équipe commerciale', 
        help='Équipe commerciale pour la recherche des adresses de livraison', readonly=False)

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
        
        # Récupérer les IDs des relations Many2many
        pricelist_ids = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_pricelist_ids')
        fiscal_position_ids = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_fiscal_position_ids')
        
        # Convertir les chaînes en listes d'IDs
        pricelist_ids = eval(pricelist_ids) if pricelist_ids else []
        fiscal_position_ids = eval(fiscal_position_ids) if fiscal_position_ids else []
        
        # Récupérer l'ID de l'équipe commerciale
        sales_team_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sales_team_id')
        
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

            slack_token=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.slack_token'),

            glovo_api_key=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.glovo_api_key'),
            glovo_api_secret=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.glovo_api_secret'),
            
            last_sync_date=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.last_sync_date', default=fields.Datetime.now()),
            
            # Nouveaux champs
            subscriber_pricelist_ids=[(6, 0, pricelist_ids)],
            subscriber_fiscal_position_ids=[(6, 0, fiscal_position_ids)],
            
            # Valeurs Sendy
            sendy_url=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_url'),
            sendy_api_key=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_api_key'),
            sendy_list_id=self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_list_id'),
            
            # Équipe commerciale
            sales_team_id=int(sales_team_id) if sales_team_id else False,
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

        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.glovo_api_key', self.glovo_api_key)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.glovo_api_secret', self.glovo_api_secret)
        
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.last_sync_date', self.last_sync_date)
        
        # Nouveaux paramètres (stockés comme chaînes de liste d'IDs)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.subscriber_pricelist_ids', 
            str(self.subscriber_pricelist_ids.ids) if self.subscriber_pricelist_ids else '[]')
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.subscriber_fiscal_position_ids', 
            str(self.subscriber_fiscal_position_ids.ids) if self.subscriber_fiscal_position_ids else '[]')

        # Paramètres Sendy
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.sendy_url', self.sendy_url)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.sendy_api_key', self.sendy_api_key)
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.sendy_list_id', self.sendy_list_id)
        
        # Équipe commerciale
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.sales_team_id', 
            self.sales_team_id.id if self.sales_team_id else False)

        super(ResConfigSettings, self).set_values()

    def getGlovoApiKey(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.glovo_api_key')
        if not odooEnv or odooEnv == 'staging':
            if value.find('[test]') == -1:
                _logger.error(f"Zacalog: odooEnv: {odooEnv}; glovo_api_key: {value}; [test] string not found in glovo_api_key.")
            else:
                return value.replace("[test]", "")
        else:
            return value
            
        return False

    def getGlovoApiSecret(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.glovo_api_secret')
        if not odooEnv or odooEnv == 'staging':
            if value.find('[test]') == -1:
                _logger.error(f"Zacalog: odooEnv: {odooEnv}; glovo_api_secret: {value}; [test] string not found in glovo_api_secret.")
            else:
                return value.replace("[test]", "")
        else:
            return value
            
        return False
    
    def getSlackToken(self):
        odooEnv = os.environ.get('ODOO_STAGE') #dev, staging or production
        value = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.slack_token')
        if not odooEnv or odooEnv == 'staging':
            if not value or value.find('[test]') == -1:
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

    def setSyncerSyncActive(self, isActive):
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.syncer_sync_active', isActive)