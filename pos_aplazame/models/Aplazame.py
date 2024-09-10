import base64, os, logging
from datetime import datetime, timedelta, time
from odoo import models, fields
import requests, re

_logger = logging.getLogger(__name__)

class Aplazame(models.Model):
    _name = 'pos_aplazame.aplazame'
    _description = 'Aplazame connector'

    POS_APIS = [
        ["cd935f926518840ebc8f733c7df965311e2e79d9", "ZM"],
        ["2d8f83dd05804e3d1ea5761dee442c67b975c050", "ZB"],
        ["b9efc29c579f9919b688d753db99dd7525d23e74", "ZP"],
        ["492b7f09a91945a9a5521c7270a083da13733202", "ZS"],
        ["7d8860d89e27774f5215da64174b45da3953ae28", "ZV"],
        ["256d08d9f4bd644617030b593572d065cb0e268f", "ZZ"]
    ]

    def _getUrl(self):
        return f"https://api.aplazame.com/"

    def _call(self, apiKey, url, postParams = None):
        baseUrl = self._getUrl() + url

        mode = ''

        hed = {
            'Authorization': f"Bearer {apiKey}",
            'Accept': f"application/vnd.aplazame{mode}.v3+json"
        }
        if postParams:
            response = requests.post(baseUrl, headers=hed, json=postParams)
        else:
            response = requests.get(baseUrl, headers=hed)
            
        if response.status_code != 200:
            if self.verbose:
                print(response.text)

        try:
            json = response.json()
        except Exception as e:
            if response.status_code == 200:
                return True
            return False

        if response.status_code != 200 and type(json) == list and not "message" in response:
            json["message"] = f"Unexpected error code {response.status_code}"

        return response.json()

    def _getOneDay(self, aDay):
        referenceDateStr = aDay.strftime('%d-%m-%Y')
        fromDay = aDay - timedelta(hours=2)

        # WEB
        apiKey = self.env['res.config.settings'].getAplazameApiKey()
        if apiKey:
            orders = self._call(apiKey, f"orders?confirmed-gte={fromDay.strftime('%Y-%m-%dT%H:%M:%SZ')}") #2015-12-22T15:09:30.537951Z
            statementId = None
            if 'results' in orders:
                for order in orders['results']:
                    orderDate = datetime.strptime(order['confirmed'].split("T")[0], '%Y-%m-%d')
                    
                    if orderDate == aDay:
                        data = {
                            'order_id': order['mid'],
                            'amount': order['total_amount']/100,
                            'date': order['confirmed']
                        }
                        statementId = self.env['zacatrus.zconta'].createStatementFromApi(
                            data, 
                            statementId, 
                            f"Aplazame WEB {referenceDateStr}",
                            48 #TODO
                        )

            if statementId:
                self.env['zacatrus.zconta'].balanceRecalc(statementId)
        else:
            msg = "Aplazame web api key not configured."
            _logger.warning(f"Zacalog: {msg}")
            return
            
    
        posList = self.env['pos.config'].search([])
        for pos in posList:
            if pos.x_aplazame_key and pos.x_shop_code:
                orders = self._call(pos.x_aplazame_key, f"orders?confirmed-gte={fromDay.strftime('%Y-%m-%dT0:0:0Z')}") #2015-12-22T15:09:30.537951Z
                
                if 'results' in orders:
                    amount = 0
                    for order in orders['results']:
                        orderDate = datetime.strptime(order['confirmed'].split("T")[0], '%Y-%m-%d')
                        if orderDate == aDay:
                            amount += order['total_amount']
                    #statementId = self._createStatement(pos.x_shop_code, order['confirmed'], amount/100, statementId)
                    if amount > 0:
                        data = {
                            'order_id': f"{pos.name}",
                            'amount': amount/100,
                            'date': order['confirmed']
                        }
                        statementId = self.env['zacatrus.zconta'].createStatementFromApi(
                            data, 
                            statementId, f"Aplazame POS { order['confirmed'].strftime('%d-%m-%Y')}", 
                            48 #TODO
                        )

    def getTransactions(self):
        lastPaylandsDate = self.env['res.config.settings'].getLastAplazameDate()

        now = datetime.now()
        maxDate = datetime.combine(now.date(), time.min) - timedelta(days=1)
        if lastPaylandsDate and lastPaylandsDate < maxDate:
            aDay = lastPaylandsDate + timedelta(days=1)
            self._getOneDay(aDay)

            self.env['res.config.settings'].setLastAplazameDate(aDay)
        else:
            msg = "Aplazame not configured or date in the future."
            _logger.warning(f"Zacalog: {msg}")


