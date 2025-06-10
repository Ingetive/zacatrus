from odoo import models, fields, api
from datetime import datetime, timedelta
import ast
import logging

_logger = logging.getLogger(__name__)

class SubscriberProcess(models.Model):
    _name = 'zacatrus.subscriber.process'
    _description = 'Process to find new subscribers'
    
    def _prepare_subscriber_data(self, partner):
        """Prépare les données d'un abonné pour Sendy"""
        return {
            'email': partner.email,
            'name': partner.name,
            'custom_fields': {
                'company': partner.company_name or '',
                'phone': partner.phone or '',
                'city': partner.city or '',
                'country': partner.country_id.name if partner.country_id else '',
            }
        }
    
    @api.model
    def send_subscribers(self):
        """
        Process that runs daily at 8:30 AM to find new customers since the last synchronization date
        and subscribes them to Sendy
        """
        # Get the last sync date from config settings
        config = self.env['res.config.settings'].create({})
        last_sync = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.last_sync_date')
        
        if not last_sync:
            last_sync = fields.Datetime.now() - timedelta(days=1)
        
        # Get the filter values for Spain
        pricelist_es_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_pricelist_es_id')
        sales_team_es_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sales_team_es_id')
        
        # Get the filter values for France
        pricelist_fr_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_pricelist_fr_id')
        sales_team_fr_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sales_team_fr_id')
        
        # Get Sendy list IDs
        b2c_es_list_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2c_es_list_id')
        b2c_fr_list_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2c_fr_list_id')
        b2b_es_list_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2b_es_list_id')
        b2b_fr_list_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_b2b_fr_list_id')
        
        # Initialize subscriber lists for each type
        b2c_es_subscribers = []
        b2c_fr_subscribers = []
        b2b_es_subscribers = []
        b2b_fr_subscribers = []
        processed_emails = set()  # Pour éviter les doublons
        
        # 1. Recherche des nouveaux clients selon les filtres configurés
        domain = [
            ('create_date', '>=', last_sync),
            ('customer_rank', '>', 0),  # Only customers
            ('email', '!=', False),     # Only customers with email
            ('email', '!=', '')         # Exclude empty emails
        ]
        
        # Recherche des partenaires
        new_customers = self.env['res.partner'].search(domain)
        es_b2b_customers = False
        fr_b2b_customers = False
        b2c_es_subscribers = []
        b2c_fr_subscribers = []

        
        # Filtrer les clients espagnols par liste de prix
        if pricelist_es_id:
            es_b2b_customers = new_customers.filtered(
                lambda p: p.property_product_pricelist.id == int(pricelist_es_id)
            )
        
        # Filtrer les clients français par liste de prix
        if pricelist_fr_id:
            fr_b2b_customers = new_customers.filtered(
                lambda p: p.property_product_pricelist.id == int(pricelist_fr_id)
            )
        
                
        for customer in es_b2b_customers:
            if customer.email and customer.email not in processed_emails:
                b2b_es_subscribers.append(self._prepare_subscriber_data(customer))
                processed_emails.add(customer.email)
                
        for customer in fr_b2b_customers:
            if customer.email and customer.email not in processed_emails:
                b2b_fr_subscribers.append(self._prepare_subscriber_data(customer))
                processed_emails.add(customer.email)
        
        # 2. Recherche des adresses de livraison des commandes des équipes commerciales
        # Pour l'Espagne
        if sales_team_es_id:
            # Rechercher les commandes de l'équipe commerciale espagnole
            sale_orders = self.env['sale.order'].search([
                ('team_id', '=', int(sales_team_es_id)),
                ('date_order', '>=', last_sync),
                ('state', 'in', ['sale', 'done'])  # Commandes confirmées ou terminées
            ])
            
            # Collecter les adresses de livraison
            for order in sale_orders:
                partner = order.partner_shipping_id
                if partner and partner.email and partner.email not in processed_emails:
                    if pricelist_es_id and partner.property_product_pricelist.id == int(pricelist_es_id):
                        b2c_es_subscribers.append(self._prepare_subscriber_data(partner))
                    else:
                        b2b_es_subscribers.append(self._prepare_subscriber_data(partner))
                    processed_emails.add(partner.email)

        # Pour la France
        if sales_team_fr_id:
            # Rechercher les commandes de l'équipe commerciale française
            sale_orders = self.env['sale.order'].search([
                ('team_id', '=', int(sales_team_fr_id)),
                ('date_order', '>=', last_sync),
                ('state', 'in', ['sale', 'done'])  # Commandes confirmées ou terminées
            ])
            
            # Collecter les adresses de livraison
            for order in sale_orders:
                partner = order.partner_shipping_id
                if partner and partner.email and partner.email not in processed_emails:
                    if pricelist_fr_id and partner.property_product_pricelist.id == int(pricelist_fr_id):
                        b2c_fr_subscribers.append(self._prepare_subscriber_data(partner))
                    else:
                        b2b_fr_subscribers.append(self._prepare_subscriber_data(partner))
                    processed_emails.add(partner.email)
        
        # Inscrire les abonnés à leurs listes Sendy respectives
        sendy = self.env['zacatrus.sendy.integration']
        total_success = 0
        
        # Inscription des clients espagnols
        if b2c_es_subscribers and b2c_es_list_id:
            success_count = sendy.bulk_subscribe_to_sendy(b2c_es_subscribers, list_id=b2c_es_list_id)
            total_success += success_count
            _logger.info(f'Subscribed {success_count} Spanish B2C customers to Sendy list {b2c_es_list_id}')
            
        if b2b_es_subscribers and b2b_es_list_id:
            success_count = sendy.bulk_subscribe_to_sendy(b2b_es_subscribers, list_id=b2b_es_list_id)
            total_success += success_count
            _logger.info(f'Subscribed {success_count} Spanish B2B customers to Sendy list {b2b_es_list_id}')
        
        # Inscription des clients français
        if b2c_fr_subscribers and b2c_fr_list_id:
            success_count = sendy.bulk_subscribe_to_sendy(b2c_fr_subscribers, list_id=b2c_fr_list_id)
            total_success += success_count
            _logger.info(f'Subscribed {success_count} French B2C customers to Sendy list {b2c_fr_list_id}')
            
        if b2b_fr_subscribers and b2b_fr_list_id:
            success_count = sendy.bulk_subscribe_to_sendy(b2b_fr_subscribers, list_id=b2b_fr_list_id)
            total_success += success_count
            _logger.info(f'Subscribed {success_count} French B2B customers to Sendy list {b2b_fr_list_id}')
        
        if not (b2c_es_subscribers or b2b_es_subscribers or b2c_fr_subscribers or b2b_fr_subscribers):
            _logger.info('No new subscribers found')
        
        # Update the last sync date to current time
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.last_sync_date', fields.Datetime.now())
        
        return True 