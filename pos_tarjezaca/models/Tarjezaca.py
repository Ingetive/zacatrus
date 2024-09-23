import base64, os, logging
from datetime import datetime, timedelta, time
from odoo import models, fields
import requests, re

_logger = logging.getLogger(__name__)

class Tarjezaca(models.Model):
    _name = 'pos_tarjezaca.tarjezaca'
    _description = 'Tarjezaca connector'

    def getTransactions(self):
        lastPaylandsDate = self.env['res.config.settings'].getLastTarjezacaDate()
        now = datetime.now()
        maxDate = datetime.combine(now.date(), time.min) - timedelta(days=1)
        if lastPaylandsDate and lastPaylandsDate < maxDate:
            aDay = lastPaylandsDate + timedelta(days=1)
            _logger.info(f"Zacalog: Tarjezaca getTransactions: proccessing {str(aDay)}.")
            
            # Tomamos un par de horas antes y después por si acaso.		
            lastDay = aDay + timedelta(days=1)
            fromDay = aDay - timedelta(hours=2)
            toDay = lastDay # + timedelta(hours=1)
            referenceDateStr = aDay.strftime('%d-%m-%Y')

            #WEB
            args = [
                ('state', 'in', ['sale']),
                ('date_order', '>=', fromDay),
                ('date_order', '<=', toDay),
                ('team_id', 'in', [6,13]),
                ('x_tarjezaca', '!=', 0)
            ]

            orders = self.env['sale.order'].search_read(args)

            webStatementId = None
            for order in orders:
                orderDate = order['date_order'].date() #datetime.strptime(order['date_order'].split(" ")[0], '%Y-%m-%d')
                
                if orderDate == aDay:
                    sign = 1
                    data = {
                        'order_id': order['client_order_ref'],
                        'amount': order['x_tarjezaca'] * sign
                    }
                    webStatementId = self.env['zacatrus.zconta'].createStatementFromApi(
                        data, 
                        webStatementId, 
                        f"Tarjezaca {referenceDateStr}",
                        62 #TODO: pasar a config
                    )

            self.env['zacatrus.zconta'].balanceRecalc(webStatementId)
            self.env['res.config.settings'].setLastTarjezacaDate(aDay)
                
            #return webStatementId
        else:
            msg = "Tarjezaca not configured or date in the future."
            _logger.warning(f"Zacalog: {msg}")
