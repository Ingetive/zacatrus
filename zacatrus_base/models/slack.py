from odoo import models, fields, api
import logging, json, requests
from .zconta import Zconta 
import datetime

_logger = logging.getLogger(__name__)

class Slackcounter(models.Model):
    _name = 'zacatrus_base.slackcounter'
    _description = 'Cola de productos a actualizar stock.'
    
    alert_type = fields.Char()
    count = fields.Integer()

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
    

    def sendFile( self, buffer, channel = False, fileName = "help" ):
        if not channel:
            channel = "C011982SJM8" #alert

        ret = False
        try:
            ret = json.loads(requests.post(
                'https://{0}/api/{1}'.format("slack.com", 'files.getUploadURLExternal'),
                data = {'filename': fileName, 'token': self.token, 'length': len(buffer)},          
            ).text)
            retPost = requests.post(ret['upload_url'], files = {'file': buffer})

            data = {'token': self.token, 'files': json.dumps([{"id": ret['file_id']}])}
            if not channel.startswith("#"):        
                data["channel_id"] = channel
            else:
                data["channel_id"] = "C072BK1AH8W"

            ret = json.loads(requests.post(
                'https://{0}/api/{1}'.format("slack.com", 'files.completeUploadExternal'),
                data = data
            ).text)

            if ret['ok'] and channel.startswith("#"):
                for file in ret['files']:
                    self.sendWarn( file['url_private_download'], channel )
        except Exception as e:
            raise(e)
    
        if ret and "ok" in ret and ret["ok"]:
            return True
        else:
            self._getLogger().error(f"sendfile {ret}")

        return False

    def sendWarnLimited( self, msg, channel = False, alertType = 'alert'):
        if not self.env['zacatrus_base.slackcounter'].search_count([('alert_type', '=', alertType)]):
            self.env['zacatrus_base.slackcounter'].create({"alert_type": alertType, "count":0})

        counters = self.env['zacatrus_base.slackcounter'].search([('alert_type', '=', alertType)])
        for counter in counters:
            if counter.count == 10:
                msg = f"Voy a parar de mandar este tipo de mensajes durante una hora para no saturar, pero puede que haya más."

            if counter.count <= 10:
                self.sendWarn( msg, channel )

            if counter.count > 8:
                if counter.create_date < datetime.datetime.now() - datetime.timedelta(minutes=60):
                    counter.unlink()
                    return
                
            counter.write({'count': counter.count + 1})
 