import base64, os, logging
from datetime import datetime, timedelta, time
from odoo import models, fields
import requests, re
from io import StringIO
import csv, re

_logger = logging.getLogger(__name__)

class Adyen(models.Model):
    _name = 'pos_paylands.adyen'
    _description = 'Adyen connector'	
	
    def getTransactions(self):
        index = self.env['res.config.settings'].getLastAdyenIndex()
        posIndex = self.env['res.config.settings'].getLastAdyenPosIndex()
        if index or posIndex:
            #Web
            loop = True
            while loop:
                index += 1
                loop = self.getIndexWeb(index)

            #POS
            loop = True
            while loop:
                posIndex += 1
                loop = self.getIndexPOS(posIndex)
        else:
            msg = "Adyen not configured."
            _logger.warning(f"Zacalog: {msg}")


    def getIndexWeb(self, index):
        res = self.getReport( index, "ZacatrusEs" )
        if res:
            webStatementId = False
            f = StringIO(res)
            reader = csv.reader(f, delimiter=',')
            idx = 0
            for row in reader:
                idx += 1
                if idx > 1:
                    rowNumber = row[3]
                    rowDebitAmount = float(row[10]) if row[10] else 0
                    rowCreditAmount = float(row[11]) if row[11] else 0
                    rowTime = row[5]
                    rowtype = row[7]
                    if rowtype in ['Settled', 'Refunded']:
                        for amount in [rowDebitAmount * -1, rowCreditAmount]:
                            if amount:
                                data = {
                                    'order_id': rowNumber,
                                    'amount': float(amount)
                                }
                                webStatementId = self.env['zacatrus.zconta'].createStatementFromApi(
                                    data, 
                                    webStatementId, 
                                    f"Adyen web report no. {index}",
                                    36 #TODO
                                )

            if webStatementId:
                self.env['zacatrus.zconta'].balanceRecalc(webStatementId)
                self.env['res.config.settings'].setLastAdyenIndex(index)
                
            return True
        return False


    def getIndexPOS(self, index):
        res = self.getReport( index, "ZacatrusPOS" )
        if res:
            f = StringIO(res)
            reader = csv.reader(f, delimiter=',')
            idx = 0
            posSessions = {}
            sessionIndexes = {}
            for row in reader:
                idx += 1
                if idx > 1:
                    #print(f"{row[3]}, {row[10]}, {row[11]}, {row[5]}, {row[7]}")
                    rowNumber = row[3]
                    rowDebitAmount = float(row[10]) if row[10] else 0
                    rowCreditAmount = float(row[11]) if row[11] else 0
                    amount = rowCreditAmount - rowDebitAmount
                    rowTime = row[5]
                    rowtype = row[7]

                    orderDate = datetime.strptime(rowTime, '%Y-%m-%d %H:%M:%S')
                    if rowtype in ['Settled', 'Refunded'] and amount:
                        if not rowNumber:						
                            sessionId = f"Unknown {index}"
                        else:
                            sessionIndexParts = rowNumber.split("-")
                            sessionIndex = f"{sessionIndexParts[0]}-{sessionIndexParts[1]}"
                            if sessionIndex in sessionIndexes:
                                sessionId = sessionIndexes[sessionIndex]
                            else:
                                args = [
                                    ('pos_reference', '=', f"Orden {rowNumber}")
                                ]
                                sessionId = f"Unknown {sessionIndex}"
                                oorders = self.env['pos.order'].search_read(args)
                                for oorder in oorders:
                                    sessionId = oorder['session_move_id'][1]
                                    sessionIndexes[sessionIndex] = sessionId

                        if sessionId:
                            if not sessionId in posSessions:
                                posSessions[sessionId] = 0
                            posSessions[sessionId] += amount

            posStatementId = False
            for sessionOriStr in posSessions:
                m = re.search(r"([0-9A-Z\/]+) \(([0-9A-Z\/]+)\)", sessionOriStr)
                if m:
                    sessionNewStr = f"{m.group(2)} {orderDate.strftime('%Y/%m/%d')}"
                else:
                    sessionNewStr = sessionOriStr
                data = {
                    'order_id': f"{sessionNewStr}",
                    'amount': float(posSessions[sessionOriStr])
                }
                posStatementId = self.env['zacatrus.zconta'].createStatementFromApi(
                    data, 
                    posStatementId, 
                    f"Adyen POS report no. {index}",
                    36 #TODO
                )

            if posStatementId:
                self.env['zacatrus.zconta'].balanceRecalc(posStatementId)
                self.env['res.config.settings'].setLastAdyenPosIndex(index)
                return True

        return res
        
    def getReport(self, number, merchant = "ZacatrusEs"):
        user = self.env['res.config.settings'].getLastAdyenReportUser() #os.getenv('ADYEN_REPORT_USER' + self.suffix)
        password = self.env['res.config.settings'].getLastAdyenReportPassword()
        if user and password:
            baseUrl = f"https://ca-live.adyen.com/reports/download/MerchantAccount/{merchant}/settlement_detail_report_batch_{number}.csv"

            session = requests.Session()
            session.auth = (user, password)

            response = session.get( baseUrl )

            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None
            else:
                fileName = f"/tmp/report{number}.html"
                with open(fileName, "w") as file1:
                    file1.write( response.text )

                _logger.error(f"Zacalog: No he podido descargar el informe {baseUrl}")
        else:
            _logger.error(f"Zacalog: Adyen user/password not configured {baseUrl}")

        return None