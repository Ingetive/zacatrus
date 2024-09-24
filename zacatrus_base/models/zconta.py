import logging
from odoo import models
import urllib

_logger = logging.getLogger(__name__)

class Zconta(models.TransientModel):
    _name = 'zacatrus.zconta'
    _description = 'Zacatrus helper conta methods'

    MADRID_LOCATION_ID = 20
    SEVILLA_LOCATION_ID = 26
    VALENCIA_LOCATION_ID = 38
    VITORIA_LOCATION_ID = 45 
    BARCELONA_LOCATION_ID = 53
    PIRAMIDES_LOCATION_ID = 103
    FERIAS_LOCATION_ID = 50
    ZARAGOZA_LOCATION_ID = 115
    VALLADOLID_LOCATION_ID = 148

    SHOPS = [
        {
            'location_id': 20,
            "code": "ZM", "zip": "28015", 
            "address": "Fernández de los Ríos, 57, 28015 Madrid", 
            "url": "http://zacatrus.es/madrid",
            "cityName": "Madrid",
            "country": "Spain",
            "postalCode": '28015',
            "details": "Local Zacatrus",
            "streetName": "Fernandez de los Rios",
            "streetNumber": 57
        },
        {
            'location_id': 26,
            "code": "ZS", "zip": "41007", 
            "address": "Luis Montoto, 121, 41007 Sevilla", 
            "url": "https://zacatrus.es/sevilla",
            "cityName": "Sevilla",
            "country": "Spain",
            "postalCode": '41007',
            "details": "Local Zacatrus",
            "streetName": "Calle Luis Montoto",
            "streetNumber": 121
        },
        {
            'location_id': 38,
            "code": "ZV", "zip": "46005", 
            "address": "Avinguda Regne de Valencia, 66, 46005 Valencia", 
            "url": "https://zacatrus.es/valencia",
            "cityName": "Valencia",
            "country": "Spain",
            "postalCode": '46005',
            "details": "Local Zacatrus",
            "streetName": "Avinguda Regne de Valencia",
            "streetNumber": 66
        },
        {
            'location_id': 45,
            "code": "ZI", "zip": "01002", 
            "address": "Urbina Kalea, 21, 01002 Vitoria", 
            "url": "https://zacatrus.es/vitoria",
            "cityName": "Vitoria-Gasteiz",
            "country": "Spain",
            "postalCode": '01002',
            "details": "Local Zacatrus",
            "streetName": "Urbina Kalea",
            "streetNumber": 21
        },
        {
            'location_id': 53,
            "code": "ZB", "zip": "08011", 
            "address": "Casanova 3, 08011 Barcelona", 
            "url": "https://zacatrus.es/barcelona",
            "cityName": "Barcelona",
            "country": "Spain",
            "postalCode": '08011',
            "details": "Local Zacatrus",
            "streetName": "Calle Casanova",
            "streetNumber": 3
        },
        {
            'location_id': 103,
            "code": "ZP", "zip": "28005", 
            "address": "Paseo de las Acacias, 67, 28005 Madrid", 
            "url": "http://zacatrus.es/madrid-piramides",
            "cityName": "Madrid",
            "country": "Spain",
            "postalCode": '28005',
            "details": "Local Zacatrus",
            "streetName": "Paseo de las Acacias",
            "streetNumber": 67
        },
        {
            'location_id': 115,
            "code": "ZZ", "zip": "50010", 
            "address": "Avenida de Madrid, 89, 50010 Zaragoza", 
            "url": "https://zacatrus.es/zaragoza",
            "cityName": "Zaragoza",
            "country": "Spain",
            "postalCode": '50010',
            "details": "Local Zacatrus",
            "streetName": "Avenida de Madrid",
            "streetNumber": 89
        },
        {
            'location_id': 148,
            "code": "ZA", "zip": "47001", 
            "address": "Marina de Escobar, 6, 47001 Valladolid", 
            "url": "https://zacatrus.es/valladolid",
            "cityName": "Valladolid",
            "country": "Spain",
            "postalCode": '47001',
            "details": "Local Zacatrus",
            "streetName": "Marina de Escobar",
            "streetNumber": 6
        }
    ]

    def getShopByZip(self, zip):
        for shop in self.SHOPS:
            if shop['zip'] == zip:
                return shop
            
        return False

    def getShopById(self, locationId):
        for shop in self.SHOPS:
            if shop['clocation_idde'] == locationId:
                return shop
            
        return False

    def getPickingSlip(self, picking_id, reportKey = "stock.report_deliveryslip"):
        cj = self.webLogin();

        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        opener.addheaders.append(('User-agent', 'Mozilla/5.0'))
        url = f"{self.url}/report/pdf/{reportKey}/{str(picking_id)}"
        request = urllib.request.Request( url )
        response = opener.open(request)

        return response.read()
    
    def createStatementFromApi(self, statementData, statementId, name, webBankJournal = 59):
        args = [
            ('payment_ref', '=', statementData['order_id']),
            ('amount', '=', statementData['amount'])
        ]
        existingLines = self.env['account.bank.statement.line'].search_read(args)
        for existingLine in existingLines:
            if existingLine['statement_id']:
                args = [
                    ('id', '=', existingLine['statement_id'][0]),
                    ('journal_id', '=', webBankJournal)
                ]
                existingStatements = self.env['account.bank.statement'].search(args)
                for statement in existingStatements:
                    return statement.id
            else:
                return False

        if not statementId:
            data = {
                'journal_id': webBankJournal,
                'name': name
            }
            statementId = self.env['account.bank.statement'].create(data).id
        
        args = [
            ("id", "=", statementId)
        ]
        statements = self.env['account.bank.statement'].search( args )
        for statement in statements:
            statement.write({ 'balance_end_real': statement['balance_start'] + statementData['amount'] })

        description = f"{statementData['order_id']}"
        line = {
            'statement_id': statementId, 
            'payment_ref': description, 'amount': statementData['amount'], 
            'journal_id': webBankJournal, 
        }
        if 'date' in statementData:
            line['date'] = statementData['date']

        self.env['account.bank.statement.line'].create(line)

        return statementId

    def balanceRecalc(self, statementId):
        if statementId:
            statements = self.env['account.bank.statement'].search([('id', '=', statementId)])
            for statement in statements:
                balanceStart = statement.balance_start
                if balanceStart == 0:
                    pargs = [('journal_id', '=', statement.journal_id.id)]
                    pfields = ['name', 'balance_start', 'balance_end_real']
                    prevs = self.env['account.bank.statement'].search_read(pargs, pfields, 1, 1, 'id DESC')
                    for prev in prevs:
                        data = {
                            'balance_start': prev['balance_end_real']
                        }
                        statement.write(data)
                        balanceStart = prev['balance_end_real']
                largs = [('statement_id', '=', statementId)]
                lines = self.env['account.bank.statement.line'].search_read(largs)
                total = 0 
                for line in lines:
                    total += line['amount']
                if not balanceStart+total == statement.balance_end_real:
                    statement.write( {'balance_end_real': balanceStart+total} )
            