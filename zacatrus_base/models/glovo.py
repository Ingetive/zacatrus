# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import models, fields, api
import requests

_logger = logging.getLogger(__name__)

class Glovo(models.TransientModel):
    _name = 'zacatrus_base.glovo'
    _description = 'Conncector de Glovo.'

    def _getBaseUrl(self):
        return f"https://api.glovoapp.com";

    def getToken(self):#, url, data = None):
        hed = {}
        data = {
            "grantType": "client_credentials",
            "clientId": self.env['res.config.settings'].getGlovoApiKey(),
            "clientSecret": self.env['res.config.settings'].getGlovoApiSecret()
        }
        try:
            tokenUrl = self._getBaseUrl() + '/oauth/token'
            response = requests.post(tokenUrl, headers=hed, json=data)
            info = response.json()
            if response.status_code == 200:
                return info["accessToken"]

            return False
        except Exception as e:
            return False
            
    def _call(self, url, data = False):
        token = self.getToken();       
        if token: 
            hed = {
               "Authorization": token
            }
            try:
                if data:
                    response = requests.post(self._getBaseUrl() + f"/v2/laas/{url}", headers=hed, json=data)
                else:
                    response = requests.get(self._getBaseUrl() + f"/v2/laas/{url}", headers=hed)
                info = response.json()

                if response.status_code >= 200 and response.status_code < 300:
                    return response.json()
                else:
                    _logger.error( f"Zacalog: Glovo: _call error {response.status_code}: {info['error']['message']}")
                return False
            except Exception as e:
                _logger.error( f"Zacalog: Glovo: " + str(e))

        return False

    def _getLocation(self, location):
        ret = {
            "cityName": location['cityName'],
            "country": location['country'],
            "postalCode": location['postalCode'],
            "rawAddress": location['address'],
            "details": location['details'],
            "streetName": location['streetName'],
            "streetNumber": location['streetNumber']
        }

        return ret
    
    def _getCreateData(self, locationId, address, details, person = "None", phone = None, email = None):
        sourceLocation = self.env['zacatrus_base.zconta'].getShopById(locationId)
        
        if not sourceLocation:
            return False

        ret = {
            'address': {
                "rawAddress": address,
                "details": details
            },
            "contact": {
                "name": person
            },
            'pickupDetails': {
                'address': sourceLocation,
                'pickupPhone': '+34675395435'
            }
        }
        if phone:
            ret['contact']['phone'] = phone
        if email:
            ret['contact']['email'] = email

        return ret
    
    def create(self, locationId, address, details = "", person = "None", phone = None, email = None):
        addresses = self._getCreateData(locationId, address, details, person, phone, email)  
        if addresses:
            response = self._call( "parcels", addresses )
            if response and response['status']['state'] == "CREATED": #SCHEDULED":
                return response['trackingNumber']
            return response
            
        return False