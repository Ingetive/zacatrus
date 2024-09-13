from odoo import models, fields, api
import logging, json, requests
from .zconta import Zconta 

_logger = logging.getLogger(__name__)

class Slack(models.TransientModel):
    _name = 'zacatrus_base.slack'
    _description = 'Sends messages to Slack.'

    def getSlackChannelByLocation(self, locationId):
        channels = {
            Zconta.MADRID_LOCATION_ID: "C03DKFTN3",
            Zconta.SEVILLA_LOCATION_ID: "C5PLLL762",
            Zconta.VALENCIA_LOCATION_ID: "CC64S5P0U",
            Zconta.VITORIA_LOCATION_ID: "CR7NDV61M",
            Zconta.BARCELONA_LOCATION_ID: "CNMJ9H70A",
            Zconta.PIRAMIDES_LOCATION_ID: "C01T5RW0J2V",
            Zconta.ZARAGOZA_LOCATION_ID: "C029CNY5J0H",
            Zconta.VALLADOLID_LOCATION_ID: "C02MK7WCY5B",
            Zconta.FERIAS_LOCATION_ID: "C06STAP9JAJ"
        }

        if locationId in channels:
            return channels[locationId]

        return None
    
    def sendWarn( self, msg, channel = False ):
        token = self.env['res.config.settings'].getSlackToken()
        if not token:
            _logger.error(f"Zacalog: Slack not configured.")
        else:
            if not channel:
                channel = "C011982SJM8" #alert

            ret = False
            try:
                url = 'https://{0}/api/{1}'.format("slack.com", 'chat.postMessage')
                ret = json.loads(requests.post(url, data = {'channel': [channel], 'text': msg, 'token': token}).text)
            except Exception as e:
                ret = False

            return ret and ret['ok']
        
        return False