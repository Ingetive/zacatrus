import base64, os, logging
from datetime import datetime, timedelta
from odoo import models, fields, api
import paramiko
from .EdiTalker import EdiTalker
import pytz

_logger = logging.getLogger(__name__)

EDI_BUNDLE_STATUS_INIT = 1
EDI_BUNDLE_STATUS_READY = 10
EDI_BUNDLE_STATUS_SENT = 20
EDI_BUNDLE_STATUS_INVOICED = 30

class BundleWizard(models.Model):
    _name = 'zacaedi.bundle'
    _description = 'Paquete de pedidos EDI a procesar completamente'
    #_inherit = 'zacaedi.bundle'

    name = fields.Char(string='name')
    order_ids = fields.Many2many('sale.order', string='Pedidos')
    file = fields.Binary("CSV file")
    status = fields.Integer()

    error_msgs = fields.Char("Errores")

    url = fields.Char("Ficheros", compute="_compute_url")
    def _compute_url(self):
        for record in self:
            record.url = '/web/content/zacaedi.bundle/%s/file/%s?download=true' % (record.id, f"bundle.zip")
    
    def _getFtp(env):
        try:
            #server = env['ir.config_parameter'].sudo().get_param('zacaedi.ftpserver')
            server = env['res.config.settings'].getSeresFtpServer()
            if not server:
                return False
            #_logger.error(f"Zacalog: Seres ftp server is {server}")
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
        bundles =  env['zacaedi.bundle'].search([('status', '=', EDI_BUNDLE_STATUS_INIT)], order="id desc", limit=1)
        for bundle in bundles:
            return bundle
        
        return env['zacaedi.bundle'].create( {'name': 'Estado EDI', 'status': EDI_BUNDLE_STATUS_INIT} )

    def loadWizard(self):
        currentBundle = BundleWizard.getCurrentBundle(self.env)

        # Assign orders not sent
        args = [
            ('x_edi_status', '=', EdiTalker.EDI_STATUS_INIT),
            ('client_order_ref', '!=', False),
            ('state', '=', 'sale'),
        ]
        orders =  self.env['sale.order'].search_read(args, order="id desc")
        orderList = []
        for order in orders:
            try:
                picking = EdiTalker.getPickingFromOrder(self.env, order)
                orderList.append( (4, order['id']) )
            except:
                pass

        #Errors to show
        errors =  self.env['zacaedi.error'].search_read([('bundle_id', '=', currentBundle.id)])
        error_msgs = ""
        for error in errors:
            error_msgs += f"{error['message']}\n"

        if not error_msgs:
            error_msgs = "No hay :-)"

        data = {'order_ids': orderList, 'error_msgs':error_msgs}
        try:
            file = EdiTalker._generateCSVs(self.env, orders, currentBundle.id)
            data['file'] = file
        except Exception as e:
            _logger.error(f"Zacalog: EDI: Cannot generate zip file: "+str(e))

        currentBundle.write(data)

        return {
            'name': 'Enviar albaranes EDI y generar CSV',
            "type" : "ir.actions.act_window",
            "res_model" : self._name,
            "view_mode": "form", 
            "res_id": currentBundle.id,
            "action": "edi_bundle_wizard",
            "view_mode": "form",
            "target": "new"
        }

    @api.model
    def sync(self):
        self.createSeresPickings()
        self.createSeresInvoices()
        self.getAllPendingOrders()

    @api.model
    def createSeresInvoices(self):
        bundles =  self.env['zacaedi.bundle'].search([('status', 'in', [EDI_BUNDLE_STATUS_READY, EDI_BUNDLE_STATUS_SENT])], order="id desc")

        idx = 0
        for bundle in bundles:
            _logger.info(f"Zacalog: EDI: Invoicing bundle {bundle['id']}...")
            isError = False
            for order in bundle.order_ids:
                if order.x_edi_status == EdiTalker.EDI_STATUS_SENT:
                    try:
                        path = self.env['ir.config_parameter'].sudo().get_param('zacaedi.invoicesoutputpath')
                        buffer = EdiTalker.saveInvoicesToSeres(self.env, order)
                        idx += 1
                        if idx == 1:
                            ftp = BundleWizard._getFtp(self.env)
                            if not ftp:
                                return
                        with ftp.file(os.path.join(path, "F"+str(order['id'])+'.txt'), "wb") as file:
                            file.write(buffer)
                        order.write({'x_edi_status': EdiTalker.EDI_STATUS_INVOICED, 'x_edi_status_updated': datetime.now()})
                    except Exception as e:
                        msg = f"No se ha podido enviar la factura del pedido {order['name']}: "+str(e)
                        _logger.error(f"Zacalog: EDI: {msg}")
                        self.env['zacatrus_base.notifier'].error("sale.order", order['id'], msg)
                        isError = True

            if not isError and bundle.status == EDI_BUNDLE_STATUS_SENT:
                bundle.write({'status': EDI_BUNDLE_STATUS_INVOICED})
                self.env['zacatrus_base.notifier'].info("zacaedi.bundle", bundle.id, "Todas las facturas enviadas.")

    @api.model
    def createSeresPickings(self):
        bundles =  self.env['zacaedi.bundle'].search([('status', '=', EDI_BUNDLE_STATUS_READY)], order="id desc")

        idx = 0
        ftp = False
        #_logger.info(f"Zacalog: EDI: Seeking bundle...")
        for bundle in bundles:
            isError = False
            #_logger.info(f"Zacalog: EDI: Sending bundle {bundle['id']}...")
            for order in bundle.order_ids:
                if order.x_edi_status == EdiTalker.EDI_STATUS_READY:
                    try:
                        path = self.env['ir.config_parameter'].sudo().get_param('zacaedi.outputpath')
                        idx += 1
                        if idx == 1:
                            ftp = BundleWizard._getFtp(self.env)
        
                        buffer = EdiTalker.savePickingsToSeres(self.env, order)
        
                        with ftp.file(os.path.join(path, str(order['id'])+'.txt'), "wb") as file:
                            file.write(buffer)
                        order.write({'x_edi_status': EdiTalker.EDI_STATUS_SENT, 'x_edi_status_updated': datetime.now()})
                    except Exception as e:
                        msg = f"No se ha podido enviar el albarán del pedido {order['name']}: " + str(e)
                        _logger.error(f"Zacalog: EDI: {msg}")
                        self.env['zacatrus_base.notifier'].error("sale.order", order['id'], msg)
                        isError = True

            if not isError:
                bundle.write({'status': EDI_BUNDLE_STATUS_SENT})
                self.env['zacatrus_base.notifier'].info("zacaedi.bundle", bundle.id, "Todos los albaranes enviados.")

    @api.model
    def getAllPendingOrders(self):
        path = self.env['ir.config_parameter'].sudo().get_param('zacaedi.inputpath') #'/lamp0/web/vhosts/estasjugando.com/recepcion/orders_d96a'
        if not path:
            return

        ftp = BundleWizard._getFtp(self.env)
        if not ftp:
            return

        fileList = ftp.listdir( path )
        ret = []

        for fileName in fileList:
            _logger.info(f"Zacalog: EDI: getting {fileName}...")
            #fileName = file.split('/')[3]
            ret.append(fileName)
            try:
                with ftp.file(os.path.join(path, fileName)) as file:
                    buffer = file.read().decode('unicode_escape')
                orders = EdiTalker.readBuffer( buffer )
                for order in orders:
                    #orderDate = datetime.strptime(order['data']['time'], "%Y%m%d")
                    #past = datetime.now() - timedelta(days=6)
                    #if orderDate < past:
                    #    msg = f"El pedido {order['data']['orderNumber']} es demasiado antiguo (>6 días) "
                    #    _logger.error (f"Zacalog: EDI: {msg}")
                    #    EdiTalker.saveError(self.env, 201, order, msg)
                    #    #TODO: Delete from ftp
                    #    #ftp.remove(os.path.join(path, fileName))
                    #    raise Exception (msg)
                    #    
                    try:
                        createdOrder = EdiTalker.createSaleOrderFromEdi( self.env, order )
                        EdiTalker.deleteError(self.env, order)
                        msg = f"Se ha creado el pedido {createdOrder.name}."
                        self.env['zacatrus_base.notifier'].info("sale.order", createdOrder.id, msg)
                    except Exception as e: 
                        msg = f"Error al leer el pedido {order['data']['orderNumber']}. Exception: " +str(e)
                        _logger.error (f"Zacalog: EDI: {msg}")
                        raise(e)
                        #self._getSlack().sendWarn( msg, "test2") #TODO:

                ftp.remove(os.path.join(path, fileName))

            except Exception as e:
                msg = f"ftp: file {fileName} could not be retrieved: " + str(e)
                self.env['zacatrus_base.notifier'].error(self._name, BundleWizard.getCurrentBundle(self.env).id, msg)
                _logger.error (f"Zacalog: EDI: {msg}")

    def sendInvoice(self):
        ids = self.env.context.get('active_ids')
        _logger.info (f"Zacalog: EDI: Send Invoice {self._name} "+ str(BundleWizard.getCurrentBundle(self.env).id))

        args = [('id', 'in', ids)]
        invoices =  self.env['sale.order'].search_read(args, order="id desc")
        for invoice in invoices:
            _logger.info (f"Zacalog: EDI: Sending invoice: {invoice['name']}")

        
        return {
            'name': 'Enviar facturas EDI',
            "type" : "ir.actions.act_window",
            "res_model" : self._name,
            "view_mode": "form",
            "res_id": BundleWizard.getCurrentBundle(self.env).id,
            "action": "edi_bundle_wizard",
            "view_mode": "form",
            "target": "new"
        }

    def send(self):
        for order in self.order_ids:
            order.write({'x_edi_status': EdiTalker.EDI_STATUS_READY, 'x_edi_status_updated': datetime.now()})
        self.write({'status': EDI_BUNDLE_STATUS_READY})
            
    @api.model
    def check(self):
        args = [('status', 'in', [EDI_BUNDLE_STATUS_READY])]
        bundles = self.env['zacaedi.invoice_bundle'].search( args )
        for bundle in bundles:
            for invoice in bundle.invoice_ids:
                args = [('name', '=', invoice['invoice_origin'])]
                orders =  self.env['sale.order'].search_read(args, order="id desc")
                hasErrors = False
                for order in orders:
                    msg = None
                    now = datetime.now(pytz.UTC)
                    orderDate = pytz.UTC.localize(datetime.strptime(order['x_edi_status_updated'], "%Y-%m-%d %H:%M:%S"))

                    if order['x_edi_status'] in [EDI_BUNDLE_STATUS_READY]:
                        sinceHours = 1
                        past = now - timedelta(sinceHours=sinceHours)
                        if orderDate < past:
                            msg = f"Error EDI: La factura {invoice['name']} no se ha enviado y se solicitó hace más de {sinceHours} hora(s)."
                            self.env['zacatrus_base.notifier'].error("account.move", invoice['id'], msg)
                            hasErrors = True

            sinceDays = 15
            past = now - datetime.timedelta(days=sinceDays)
            if orderDate < past and not hasErrors:
                msg = f"El paquete {bundle.id} tiene más de {sinceDays} días. Lo damos por cerrado."
                self.env['zacatrus_base.notifier'].warn("zacaedi.bundle", bundle.id, msg)
                _logger.warning(f"Zacalog: EDI: {msg}")                    
                self.env['zacaedi.invoice_bundle'].write (bundle.id, {'status': EDI_BUNDLE_STATUS_INVOICED})


        args = [('status', 'in', [EDI_BUNDLE_STATUS_READY, EDI_BUNDLE_STATUS_SENT])]
        bundles = self.env['zacaedi.bundle'].search( args )
        for bundle in bundles:
            now = datetime.now(pytz.UTC)
            oargs = [('id','in',bundle.order_ids)]
            orders = self.env['sale.order'].search_read( oargs )
            hasErrors = False
            orderDate = False
            for order in orders:
                if order['x_edi_status_updated']:
                    orderDate = pytz.UTC.localize(datetime.strptime(order['x_edi_status_updated'], "%Y-%m-%d %H:%M:%S"))
                else:
                    orderDate = pytz.UTC.localize(datetime.strptime(order['create_date'], "%Y-%m-%d %H:%M:%S"))
                    
                if order['client_order_ref']:
                    msg = None   
                    if order['x_edi_status'] in [EdiTalker.EDI_STATUS_INIT]:
                        sinceDays = 2
                        past = now - timedelta(days=sinceDays)
                        if orderDate < past:
                            msg = f"Error EDI: El pedido {order['name']} no se ha procesado y se creó hace más de {sinceDays} días."
                            self.env['zacatrus_base.notifier'].error("sale.order", order['id'], msg)
                            hasErrors = True
                    elif order['x_edi_status'] in [EDI_BUNDLE_STATUS_READY]:
                        sinceHours = 1
                        past = now - timedelta(hours=sinceHours)
                        if orderDate < past:
                            msg = f"Error EDI: El pedido {order['name']} no se ha enviado y está listo desde hace más de {sinceHours} hora(s)."
                            self.env['zacatrus_base.notifier'].error("sale.order", order['id'], msg)
                            hasErrors = True
                    elif order['x_edi_status'] in [EdiTalker.EDI_STATUS_SENT]:
                        sinceHours = 1
                        past = now - timedelta(hours=sinceHours)
                        if orderDate < past:
                            hasErrors = True
                            if order['invoice_status'] != 'invoiced':
                                msg = f"Error EDI: El pedido {order['name']} no tiene factura y está enviado desde hace más de {sinceHours} hora(s)."
                            else:
                                msg = f"Error EDI: La factura del pedido {order['name']} no se ha enviado y el pedido se envió hace más de {sinceHours} hora(s)."
                            self.env['zacatrus_base.notifier'].error("sale.order", order['id'], msg)
                
            sinceDays = 15
            past = now - timedelta(days=sinceDays)
            if orderDate and orderDate < past and not hasErrors:
                msg = f"El paquete {bundle.id} tiene más de {sinceDays} días. Lo damos por cerrado."
                self.env['zacatrus_base.notifier'].warn("zacaedi.bundle", bundle.id, msg)
                _logger.warning(f"Zacalog: EDI: {msg}")  
                self.env['zacaedi.bundle'].write (bundle.id, {'status': EDI_BUNDLE_STATUS_INVOICED})                
