import requests
import logging
from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SendyIntegration(models.AbstractModel):
    _name = 'zacatrus.sendy.integration'
    _description = 'Intégration avec Sendy pour la gestion des abonnés'

    @api.model
    def _get_sendy_config(self):
        """Récupère la configuration Sendy depuis les paramètres système"""
        sendy_url = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_url')
        sendy_api_key = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_api_key')
        sendy_list_id = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.sendy_list_id')

        if not all([sendy_url, sendy_api_key, sendy_list_id]):
            raise UserError('La configuration Sendy est incomplète. Veuillez vérifier les paramètres.')

        return sendy_url, sendy_api_key, sendy_list_id

    @api.model
    def subscribe_to_sendy(self, email, name='', custom_fields=None):
        """
        Inscrit un email à la liste Sendy
        :param email: Email à inscrire
        :param name: Nom de l'abonné (optionnel)
        :param custom_fields: Dictionnaire de champs personnalisés (optionnel)
        :return: True si succès, False sinon
        """
        try:
            sendy_url, sendy_api_key, sendy_list_id = self._get_sendy_config()
            
            # Préparer les données
            data = {
                'api_key': sendy_api_key,
                'list': sendy_list_id,
                'email': email,
                'boolean': 'true'  # Pour recevoir une réponse true/false
            }
            
            if name:
                data['name'] = name
                
            if custom_fields:
                for key, value in custom_fields.items():
                    data[key] = value

            # Envoyer la requête à Sendy
            response = requests.post(
                f"{sendy_url}/subscribe",
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                response_text = response.text.lower()
                if 'true' in response_text or 'already exists' in response_text:
                    _logger.info(f'Inscription réussie pour {email}')
                    return True
                else:
                    _logger.error(f'Erreur lors de l\'inscription de {email}: {response.text}')
            else:
                _logger.error(f'Erreur HTTP {response.status_code} pour {email}')

        except Exception as e:
            _logger.error(f'Erreur lors de l\'inscription à Sendy: {str(e)}')
        
        return False

    @api.model
    def bulk_subscribe_to_sendy(self, subscribers):
        """
        Inscrit plusieurs abonnés à la liste Sendy
        :param subscribers: Liste de dictionnaires contenant email, name et custom_fields
        :return: Nombre d'inscriptions réussies
        """
        success_count = 0
        for subscriber in subscribers:
            if self.subscribe_to_sendy(
                email=subscriber.get('email'),
                name=subscriber.get('name', ''),
                custom_fields=subscriber.get('custom_fields', {})
            ):
                success_count += 1
        
        return success_count 