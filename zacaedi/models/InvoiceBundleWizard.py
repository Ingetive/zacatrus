import base64, os, logging
from datetime import datetime, timedelta
from odoo import models, fields, api
import paramiko
from .EdiTalker import EdiTalker

_logger = logging.getLogger(__name__)

EDI_BUNDLE_STATUS_INIT = 1
EDI_BUNDLE_STATUS_READY = 10
EDI_BUNDLE_STATUS_SENT = 20
EDI_BUNDLE_STATUS_INVOICED = 30

class InvoiceBundleWizard(models.Model):
    _name = 'zacaedi.invoice_bundle'
    _description = 'Paquete de facturas a enviar a EDI'

    invoice_ids = fields.Many2many('account.move', string='Facturas')
    status = fields.Integer()

    error_msgs = fields.Char("Errores")
    
    def _getFtp(env):
        try:
            server = env['ir.config_parameter'].sudo().get_param('zacaedi.ftpserver')
            user = env['ir.config_parameter'].sudo().get_param('zacaedi.ftpuser')
            password = env['ir.config_parameter'].sudo().get_param('zacaedi.ftppassword')
            
            transport = paramiko.Transport((server, 22))
            transport.connect(None, user, password)
            if transport:
                return paramiko.SFTPClient.from_transport(transport)
            else:
                _logger.error("Zacalog: EDI: Cannot connect to sftp.")
        except Exception as err:
            raise Exception(err)
        
    def getCurrentBundle(env):        
        return env['zacaedi.invoice_bundle'].create( {'status': EDI_BUNDLE_STATUS_INIT} )


    @api.model
    def sync(self):
        bundles =  self.env['zacaedi.invoice_bundle'].search([('status', 'in', [EDI_BUNDLE_STATUS_READY])], order="id desc")
        idx = 0
        for bundle in bundles:
            isError = False
            for invoice in bundle.invoice_ids:
                args = [('name', '=', invoice['invoice_origin'])]
                orders =  self.env['sale.order'].search(args, order="id desc")
                for order in orders:
                    if order.x_edi_status == EdiTalker.EDI_STATUS_READY:
                        try:
                            path = self.env['ir.config_parameter'].sudo().get_param('zacaedi.invoicesoutputpath')
                            buffer = EdiTalker.saveInvoicesToSeres(self.env, order, True)
                            idx += 1
                            if idx == 1:
                                ftp = InvoiceBundleWizard._getFtp(self.env)
                            with ftp.file(os.path.join(path, "F"+str(order['id'])+'.txt'), "wb") as file:
                                file.write(buffer)
                            order.write({'x_edi_status': EdiTalker.EDI_STATUS_INVOICED, 'x_edi_status_updated': datetime.now()})
                        except Exception as e:
                            msg = f"Could not send invoice for order {order['name']}: "+str(e)
                            _logger.error(f"Zacalog: EDI: {msg}")
                            self.env['zacatrus_base.notifier'].error("sale.order", order['id'], msg)
                            isError = True

            if not isError:
                bundle.write({'status': EDI_BUNDLE_STATUS_INVOICED})
                self.env['zacatrus_base.notifier'].info("zacaedi.invoice_bundle", bundle.id, "Todas las facturas enviadas.")

    def loadWizard(self):
        ids = self.env.context.get('active_ids')
        currentInvoiceBundle = InvoiceBundleWizard.getCurrentBundle(self.env)
        _logger.info (f"Zacalog: EDI: Send Invoice {self._name} "+ str(currentInvoiceBundle['id']))

        args = [('id', 'in', ids)]
        invoices =  self.env['account.move'].search_read(args, order="id desc")
        invoiceList = []
        error_msgs = ""
        for invoice in invoices:
            if not invoice['invoice_origin']:
                msg = f"No encuentro el pedido para la factura {invoice['name']}"
                error_msgs += f"{msg}\n"
                _logger.warning (msg)
            else:
                try:
                    invoiceList.append( (4, invoice['id']) )
                except:
                    pass

        data = {'invoice_ids': invoiceList, 'error_msgs':error_msgs}
        currentInvoiceBundle.write(data)
        
        return {
            'name': 'Enviar facturas EDI',
            "type" : "ir.actions.act_window",
            "res_model" : self._name,
            "view_mode": "form",
            "res_id": currentInvoiceBundle['id'],
            "action": "edi_invoice_bundle_wizard",
            "view_mode": "form",
            "target": "new"
        }

    def send(self):
        for invoice in self.invoice_ids:
            args = [('name', '=', invoice['invoice_origin'])]
            orders =  self.env['sale.order'].search(args, order="id desc")
            for order in orders:
                if not order['x_edi_status']:
                    order.write({'x_edi_status': EdiTalker.EDI_STATUS_READY, 'x_edi_status_updated': datetime.now()})
                else:
                    _logger.error(f"Zacalog: EDI: El pedido {order['name']} ya se estaba procesando.")

        self.write({'status': EDI_BUNDLE_STATUS_READY})
        