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

class BundleWizard(models.Model):
    _name = 'zacaedi.bundle'
    #_inherit = 'zacaedi.bundle'

    name = fields.Char(string='name')
    order_ids = fields.Many2many('sale.order', string='Pedidos')
    file = fields.Binary("CSV file")
    status = fields.Integer()

    error_msgs = fields.Char("Errores")

    url = fields.Char("Ficheros", compute="_compute_url")
    def _compute_url(self):
        for record in self:
            record.url = '/web/content/zacaedi.bundle/%s/file/%s?download=true' % (self.id, f"bundle.zip")
    
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
        bundles =  env['zacaedi.bundle'].search([('status', '=', EDI_BUNDLE_STATUS_INIT)], order="id desc", limit=1)
        for bundle in bundles:
            return bundle
        
        return env['zacaedi.bundle'].create( {'name': 'Estado EDI', 'status': EDI_BUNDLE_STATUS_INIT} )

    def loadWizard(self):
        currentBundle = BundleWizard.getCurrentBundle(self.env)

        # Assign orders not sent
        args = [
            ('x_edi_status', '=', EdiTalker.EDI_STATUS_INIT),
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
        errors =  self.env['zacaedi.error'].search_read([('bundle_id', '=', currentBundle['id'])])
        error_msgs = ""
        for error in errors:
            error_msgs += f"{error['message']}\n"

        if not error_msgs:
            error_msgs = "No hay :-)"

        data = {'order_ids': orderList, 'error_msgs':error_msgs}
        try:
            file = EdiTalker._generateCSVs(self.env, orders, currentBundle['id'])
            data['file'] = file
        except Exception as e:
            _logger.info(f"Zacalog: EDI: Cannot generate zip file: "+str(e))

        currentBundle.write(data)

        return {
            'name': 'Enviar albaranes EDI y generar CSV',
            "type" : "ir.actions.act_window",
            "res_model" : self._name,
            "view_mode": "form", 
            "res_id": currentBundle['id'],
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
                        with ftp.file(os.path.join(path, "F"+str(order['id'])+'.txt'), "wb") as file:
                            file.write(buffer)
                        order.write({'x_edi_status': EdiTalker.EDI_STATUS_INVOICED})
                    except Exception as e:
                        _logger.error(f"Zacalog: EDI: Courld not send invoice for order {order['name']}: "+str(e))
                        isError = True

            if not isError and bundle.status == EDI_BUNDLE_STATUS_SENT:
                bundle.write({'status': EDI_BUNDLE_STATUS_INVOICED})

    @api.model
    def createSeresPickings(self):
        bundles =  self.env['zacaedi.bundle'].search([('status', '=', EDI_BUNDLE_STATUS_READY)], order="id desc")

        idx = 0
        ftp = False
        _logger.info(f"Zacalog: EDI: Seeking bundle...")
        for bundle in bundles:
            isError = False
            _logger.info(f"Zacalog: EDI: Sending bundle {bundle['id']}...")
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
                        order.write({'x_edi_status': EdiTalker.EDI_STATUS_SENT})
                    except Exception as e:
                        _logger.error(f"Zacalog: EDI: Courld not send order {order['name']}...")
                        isError = True

            if not isError:
                bundle.write({'status': EDI_BUNDLE_STATUS_SENT})

    @api.model
    def getAllPendingOrders(self):
        path = self.env['ir.config_parameter'].sudo().get_param('zacaedi.inputpath') #'/lamp0/web/vhosts/estasjugando.com/recepcion/orders_d96a'
        if not path:
            return

        ftp = BundleWizard._getFtp(self.env)

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
                    orderDate = datetime.strptime(order['data']['time'], "%Y%m%d")
                    past = datetime.now() - timedelta(days=6)
                    if orderDate < past:
                        msg = "El pedido es demasiado antiguo (>6 días) "
                        _logger.error (f"Zacalog: EDI: {msg}")
                        EdiTalker.saveError(self.env, 201, order, msg)
                        #TODO: Delete from ftp
                        #ftp.remove(os.path.join(path, fileName))
                        raise Exception (msg)
                        
                    try:
                        EdiTalker.createSaleOrderFromEdi( self.env, order )
                        EdiTalker.deleteError(self.env, order)
                    except Exception as e: 
                        msg = "Zacalog: EDI: getOrdersFromSeres. Exception: " +str(e)
                        _logger.error (msg)
                        raise(e)
                        #self._getSlack().sendWarn( msg, "test2") #TODO:

                ftp.remove(os.path.join(path, fileName))

            except Exception as e:
                _logger.error (f"Zacalog: EDI: ftp: file {fileName} could not be retrieved: " + str(e))

    def send(self):
        for order in self.order_ids:
            order.write({'x_edi_status': EdiTalker.EDI_STATUS_READY})
        self.write({'status': EDI_BUNDLE_STATUS_READY})
        