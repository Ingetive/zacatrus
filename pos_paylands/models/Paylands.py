import base64, os, logging
from datetime import datetime, timedelta
from odoo import models, fields
import requests, re

_logger = logging.getLogger(__name__)

EDI_BUNDLE_STATUS_INIT = 1
EDI_BUNDLE_STATUS_READY = 10
EDI_BUNDLE_STATUS_SENT = 20
EDI_BUNDLE_STATUS_INVOICED = 30

class Paylands(models.Model):
    _name = 'pos_paylands.paylands'
    _description = 'Paylands connector'

    def getTransactions(self):
        lastPaylandsDate = self.env['res.config.settings'].getLastPaylandsDate()
        if lastPaylandsDate:
            _logger.info(f"Zacalog: Paylands getting transactions from {lastPaylandsDate}")
            aDay = lastPaylandsDate + timedelta(days=1)
            
            self._getOneDay(aDay)
            #self.setDbKey("last_paylands_date", aDay)
            self.env['res.config.settings'].setLastPaylandsDate(aDay)


    def _getOneDay(self, aDay):		
        referenceDateStr = aDay.strftime('%d-%m-%Y')
        lastDay = aDay + timedelta(days=1)
        fromDay = aDay - timedelta(hours=2)
        toDay = lastDay # + timedelta(hours=1)

        #WEB
        call = f"orders?start={fromDay.strftime('%Y%m%d%H00')}&end={toDay.strftime('%Y%m%d%H00')}"
        res = self._call( call )
    
        webStatementId = None
        posSessions = {}
        sessionIndexes = {}
        
        if not res['code'] == 200:
            _logger.error(f"Zacalog: Paylands res " + str(res))
        else:
            if res['count'] > 0:
                for order in res['transactions']:
                    orderDate = datetime.strptime(order['created'].split(" ")[0], '%Y-%m-%d')

                    if orderDate == aDay:             
                        service = self.env['pos_paylands.service'].getNameByCode(order['serviceUUID'])
                        #_logger.info(f"Zacalog: Paylands getting transactions service: {service}")

                        sign = 1
                        if order['type'] == 'REFUND':
                            sign = -1
                        data = {
                            'order_id': order['additional'],
                            'amount': order['amount']/100 * sign
                        }

                        if order['status'] not in ['CANCELLED', 'ERROR', 'REFUSED', 'PENDING']:
                            #print(f"{order['orderUUID']} ({service})-> {order['additional']}")
                            if service == "Web":
                                webStatementId = self.createStatementFromApi(
                                    data, 
                                    webStatementId, 
                                    f"PNP {service} {referenceDateStr}",
                                    59 #TODO: pasar a config
                                )
                            elif service.startswith('POS'):
                                sessionId = False
                                if not order['additional']:
                                    sessionId = f"Unknown {service} {referenceDateStr}"
                                else:
                                    sessionIndexParts = order['additional'].split("-")
                                    sessionIndex = f"{sessionIndexParts[0]}-{sessionIndexParts[1]}"
                                    if sessionIndex in sessionIndexes:
                                        sessionId = sessionIndexes[sessionIndex]
                                    else:
                                        args = [
                                            ('pos_reference', 'in', [f"Orden {order['additional']}", f"Pedido {order['additional']}"])
                                        ]
                                        oorders = self.env['pos.order'].search_read(args)
                                        for oorder in oorders:
                                            if not oorder['session_move_id']:
                                                msg = f"Paylands: Pos order {oorder['name']} has not session_move_id."
                                                raise Exception( msg )
                                            else:
                                                sessionId = oorder['session_move_id'][1]
                                                sessionIndexes[sessionIndex] = sessionId

                                if sessionId:
                                    if not sessionId in posSessions:
                                        posSessions[sessionId] = 0

                                    posSessions[sessionId] += order['amount'] * sign

            if webStatementId:
                self.balanceRecalc(webStatementId)

            posStatementId = None
            for sessionOriStr in posSessions:
                m = re.search(r"([0-9A-Z\/]+) \(([0-9A-Z\/]+)\)", sessionOriStr)
                if m:
                    sessionNewStr = f"{m.group(2)}"
                else:
                    sessionNewStr = sessionOriStr

                data = {
                    'order_id': f"{sessionNewStr}",
                    'amount': posSessions[sessionOriStr]/100
                }
                posStatementId = self.createStatementFromApi(data, posStatementId, f"PNP POS {referenceDateStr}")

            if posStatementId:
                self.balanceRecalc(posStatementId)
            
        return True

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
            statementId = self.env['account.bank.statement'].create(data)
        
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
                    pargs = [('journal_id', '=', statement.journal_id[0])]
                    pfields = ['name', 'balance_start', 'balance_end_real']
                    prevs = self.env['account.bank.statement'].search_read(pargs, pfields, 1, 1, 'id DESC')
                    for prev in prevs:
                        if fix:
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
                                   
    def _getUrl(self):
        envString = ""
        sandboxMode = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_sandbox_mode')
        if sandboxMode:
            envString = "/sandbox"
        return f"https://api.paylands.com/v1{envString}/"

    def _call(self, url, postParams = None):
        baseUrl = self._getUrl() + url

        apiKey = self.env['res.config.settings'].getPaylandsApiKey()
        #apiKey = self.env['ir.config_parameter'].sudo().get_param('pos_paylands.paylands_apikey')

        hed = {'Authorization': 'Bearer ' + apiKey}
        if postParams:
            response = requests.post(baseUrl, headers=hed, json=postParams)
        else:
            response = requests.get(baseUrl, headers=hed)
            
        try:
            json = response.json()
        except Exception as e:
            if response.status_code == 200:
                #print("Error parsing response json getting stock from Magento: " + url)
                #print(response.text)
                return True
            return False

        if response.status_code != 200 and type(json) == list and not "message" in response:
            json["message"] = f"Unexpected error code {response.status_code}"

        return response.json()