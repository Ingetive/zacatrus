from odoo import models, fields, api
from datetime import datetime, timedelta
import ast
import logging

_logger = logging.getLogger(__name__)

class SubscriberProcess(models.Model):
    _name = 'zacatrus_subscriber_process'
    _description = 'Process to find new subscribers'
    
    def _prepare_subscriber_data(self, partner):
        """Prépare les données d'un abonné pour Sendy"""
        custom_fields = {
            'company': partner.company_name or '',
            'phone': partner.phone or '',
            'city': partner.city or '',
            'country': partner.country_id.code if partner.country_id else '',
        }
        
        # Ajouter le premier mot du POS s'il est défini
        if partner.pos:
            #pos_first_word = partner.pos.split()[0] if partner.pos else ''
            custom_fields['pos'] = partner.pos
            
        return {
            'email': partner.email,
            'name': partner.name,
            'custom_fields': custom_fields
        }
    
    @api.model
    def updatePos(self, fromDate = False):
        # Rechercher les commandes POS récentes
        domain = [
            ('partner_id', '!=', False),
            ('config_id', '!=', False)
        ]
        
        if fromDate:
            domain.append(('date_order', '>=', fromDate))
            
        # Rechercher les commandes POS
        orders = self.env['pos.order'].search(domain, order='date_order desc')
        
        # Pour chaque commande, mettre à jour le client si nécessaire
        for order in orders:
            partner = order.partner_id
            if partner and partner.property_product_pricelist.id == 3:
                if not partner.pos or '(' in partner.pos:
                    # Extraire le nom du POS sans l'utilisateur
                    pos_name = order.config_id.name.split('(')[0].strip()
                    partner.write({'pos': pos_name})
        
    
    @api.model
    def send_subscribers(self):
        """
        Process that runs daily at 8:30 AM to find new customers since the last synchronization date
        and subscribes them to Sendy
        """
        
        last_sync = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.last_sync_date')
        
        if not last_sync:
            last_sync = fields.Datetime.now() - timedelta(days=1)
        
        self.updatePos(last_sync)
        
        # Get the filter values for Spain
        pricelist_es_ids_str = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_pricelist_es_ids', '')
        sales_team_es_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sales_team_es_id')
        
        # Get the filter values for France
        pricelist_fr_ids_str = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_pricelist_fr_ids', '')
        sales_team_fr_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sales_team_fr_id')
        
        # Convert string IDs to list of integers
        pricelist_es_ids = [int(x) for x in pricelist_es_ids_str.split(',') if x.strip()]
        pricelist_fr_ids = [int(x) for x in pricelist_fr_ids_str.split(',') if x.strip()]
        
        # Convert team IDs to integers
        sales_team_es_id = int(sales_team_es_id) if sales_team_es_id else False
        sales_team_fr_id = int(sales_team_fr_id) if sales_team_fr_id else False
        
        # Get Sendy list IDs
        b2c_es_list_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2c_es_list_id')
        b2c_fr_list_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2c_fr_list_id')
        
        # Get B2B list IDs (comma-separated strings)
        b2b_es_list_ids = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2b_es_list_ids', '')
        b2b_fr_list_ids = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2b_fr_list_ids', '')
        
        # Convert string to list
        b2b_es_lists = [x.strip() for x in b2b_es_list_ids.split(',') if x.strip()] if b2b_es_list_ids else []
        b2b_fr_lists = [x.strip() for x in b2b_fr_list_ids.split(',') if x.strip()] if b2b_fr_list_ids else []
        
        # Initialize subscriber lists for each type
        b2b_es_subscribers = []
        b2b_fr_subscribers = []
        b2c_es_subscribers = []
        b2c_fr_subscribers = []
        # Recherche des partenaires
        es_b2b_customers = False
        fr_b2b_customers = False
        processed_emails = set()  # Pour éviter les doublons
        
        # 1. Recherche des nouveaux clients selon les filtres configurés
        domain = [
            ('write_date', '>=', last_sync),
            ('email', '!=', False),     # Only customers with email
            ('email', '!=', '')         # Exclude empty emails
        ]
                
        # Filtrer les clients espagnols par liste de prix
        if pricelist_es_ids:
            new_customers = self.env['res.partner'].search(domain)
            es_b2b_customers = new_customers.filtered(
                lambda p: p.property_product_pricelist.id in pricelist_es_ids
            )
            for customer in es_b2b_customers:
                if customer.email and customer.email not in processed_emails:
                    b2b_es_subscribers.append(self._prepare_subscriber_data(customer))
                    processed_emails.add(customer.email)
        
        # Filtrer les clients français par liste de prix
        if pricelist_fr_ids:
            new_customers = self.env['res.partner'].search(domain)
            fr_b2b_customers = new_customers.filtered(
                lambda p: p.property_product_pricelist.id in pricelist_fr_ids
            )
            for customer in fr_b2b_customers:
                if customer.email and customer.email not in processed_emails:
                    b2b_fr_subscribers.append(self._prepare_subscriber_data(customer))
                    processed_emails.add(customer.email)    
        
        # 2. Recherche des adresses de livraison des commandes des équipes commerciales
        # Pour l'Espagne
        if sales_team_es_id:
            # Rechercher les commandes de l'équipe commerciale espagnole
            sale_orders = self.env['sale.order'].search([
                ('team_id', '=', sales_team_es_id),
                ('write_date', '>=', last_sync),
                ('state', 'in', ['sale', 'done'])  # Commandes confirmées ou terminées
            ])
            
            # Collecter les adresses de livraison
            for order in sale_orders:
                partner = order.partner_shipping_id
                if partner and partner.email and partner.email not in processed_emails:
                    b2c_es_subscribers.append(self._prepare_subscriber_data(partner))
                    processed_emails.add(partner.email)

        # Pour la France
        if sales_team_fr_id:
            # Rechercher les commandes de l'équipe commerciale française
            sale_orders = self.env['sale.order'].search([
                ('team_id', '=', sales_team_fr_id),
                ('write_date', '>=', last_sync),
                ('state', 'in', ['sale', 'done'])  # Commandes confirmées ou terminées
            ])
            
            # Collecter les adresses de livraison
            for order in sale_orders:
                partner = order.partner_shipping_id
                if partner and partner.email and partner.email not in processed_emails:
                    b2c_fr_subscribers.append(self._prepare_subscriber_data(partner))
                    processed_emails.add(partner.email)

        # 3. Recherche des clients avec tarif Zacasocio et code barre 242
        zacasocio_customers = self.env['res.partner'].search([
            ('property_product_pricelist', '=', 3),
            ('write_date', '>=', last_sync),
            ('email', '!=', False),
            ('email', '!=', '')
        ])
        
        # Filtrer les clients par code barre
        for customer in zacasocio_customers:
            if customer.barcode and customer.barcode.startswith('242') and customer.email not in processed_emails:
                ## Déterminer si le client est espagnol ou français
                #if customer.country_id and customer.country_id.code == 'ES':
                #    b2c_es_subscribers.append(self._prepare_subscriber_data(customer))
                #elif customer.country_id and customer.country_id.code == 'FR':
                #    b2c_fr_subscribers.append(self._prepare_subscriber_data(customer))
                b2c_es_subscribers.append(self._prepare_subscriber_data(customer))
                processed_emails.add(customer.email)
        
        # Inscrire les abonnés à leurs listes Sendy respectives
        sendy = self.env['zacatrus.sendy.integration']
        total_success = 0
        
        # Inscription des clients espagnols
        if b2c_es_subscribers and b2c_es_list_id:
            success_count = sendy.bulk_subscribe_to_sendy(b2c_es_subscribers, list_id=b2c_es_list_id)
            total_success += success_count
            _logger.info(f'Subscribed {success_count} Spanish B2C customers to Sendy list {b2c_es_list_id}')
            
        if b2b_es_subscribers and b2b_es_lists:
            for list_id in b2b_es_lists:
                success_count = sendy.bulk_subscribe_to_sendy(b2b_es_subscribers, list_id=list_id)
                total_success += success_count
                _logger.info(f'Subscribed {success_count} Spanish B2B customers to Sendy list {list_id}')
        
        # Inscription des clients français
        if b2c_fr_subscribers and b2c_fr_list_id:
            success_count = sendy.bulk_subscribe_to_sendy(b2c_fr_subscribers, list_id=b2c_fr_list_id)
            total_success += success_count
            _logger.info(f'Subscribed {success_count} French B2C customers to Sendy list {b2c_fr_list_id}')
            
        if b2b_fr_subscribers and b2b_fr_lists:
            for list_id in b2b_fr_lists:
                success_count = sendy.bulk_subscribe_to_sendy(b2b_fr_subscribers, list_id=list_id)
                total_success += success_count
                _logger.info(f'Subscribed {success_count} French B2B customers to Sendy list {list_id}')
        
        if not (b2c_es_subscribers or b2b_es_subscribers or b2c_fr_subscribers or b2b_fr_subscribers):
            _logger.info('No new subscribers found')
        
        # Update the last sync date to current time
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.last_sync_date', fields.Datetime.now())
        
        return True 