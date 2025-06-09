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
        
        # Get the filter values
        pricelist_ids_str = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_pricelist_ids', '[]')
        fiscal_position_ids_str = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.subscriber_fiscal_position_ids', '[]')
        sales_team_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sales_team_id')
        
        pricelist_ids = ast.literal_eval(pricelist_ids_str)
        fiscal_position_ids = ast.literal_eval(fiscal_position_ids_str)
        
        subscribers = []
        processed_emails = set()  # Pour éviter les doublons
        
        # 1. Recherche des nouveaux clients selon les filtres configurés
        domain = [
            ('create_date', '>=', last_sync),
            ('customer_rank', '>', 0),  # Only customers
            ('email', '!=', False),     # Only customers with email
            ('email', '!=', '')         # Exclude empty emails
        ]
        
        if pricelist_ids:
            domain.append(('property_product_pricelist', 'in', pricelist_ids))
            
        if fiscal_position_ids:
            domain.append(('property_account_position_id', 'in', fiscal_position_ids))
        
        new_customers = self.env['res.partner'].search(domain)
        
        # Ajouter les nouveaux clients à la liste des abonnés
        for customer in new_customers:
            if customer.email and customer.email not in processed_emails:
                subscribers.append(self._prepare_subscriber_data(customer))
                processed_emails.add(customer.email)
        
        # 2. Recherche des adresses de livraison des commandes de l'équipe commerciale
        sale_orders = []
        if sales_team_id:
            # Rechercher les commandes de l'équipe commerciale
            sale_orders = self.env['sale.order'].search([
                ('team_id', '=', int(sales_team_id)),
                ('date_order', '>=', last_sync),
                ('state', 'in', ['sale', 'done'])  # Commandes confirmées ou terminées
            ])
            
            # Collecter les adresses de livraison
            for order in sale_orders:
                partner = order.partner_shipping_id
                if partner and partner.email and partner.email not in processed_emails:
                    subscribers.append(self._prepare_subscriber_data(partner))
                    processed_emails.add(partner.email)
        
        # Inscrire tous les abonnés à Sendy
        if subscribers:
            sendy = self.env['zacatrus.sendy.integration']
            success_count = sendy.bulk_subscribe_to_sendy(subscribers)
            
            _logger.info(
                f'Processed {len(new_customers)} new customers and {len(sale_orders)} delivery addresses, '
                f'{success_count} successfully subscribed to Sendy'
            )
        else:
            _logger.info('No new subscribers found')
        
        # Update the last sync date to current time
        self.env['ir.config_parameter'].sudo().set_param('zacatrus_base.last_sync_date', fields.Datetime.now())
        
        return True 