import base64, os, logging
from datetime import datetime, timedelta
from odoo import models, fields, api
import paramiko
from .EdiTalker import EdiTalker
from .EdiWriter import EdiWriter

_logger = logging.getLogger(__name__)

EDI_BUNDLE_STATUS_INIT = 1

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
        orders =  self.env['sale.order'].search_read([('x_edi_status', '=', EdiWriter.EDI_STATUS_INIT)], order="id desc")
        orderList = []
        for order in orders:
            orderList.append( (4, order['id']) )

        #Errors to show
        errors =  self.env['zacaedi.error'].search_read([('bundle_id', '=', currentBundle['id'])])
        error_msgs = ""
        for error in errors:
            error_msgs += f"{error['message']}\n"

        if not error_msgs:
            error_msgs = "No hay :-)"

        
        file = EdiWriter._generateCSVs(self.env, orders, currentBundle['id'])
        currentBundle.write({'order_ids': orderList, 'error_msgs':error_msgs, 'file': file})


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
    def getAllPendingOrders(self):
        path = self.env['ir.config_parameter'].sudo().get_param('zacaedi.inputpath') #'/lamp0/web/vhosts/estasjugando.com/recepcion/orders_d96a'

        ftp = BundleWizard._getFtp(self.env)

        fileList = ftp.listdir( path )
        ret = []

        for fileName in fileList:
            _logger.info(f"Zacalog: EDI: getting {fileName}...")
            #fileName = file.split('/')[3]
            ret.append(fileName)
            try:
                file = ftp.file(
                    os.path.join(path, fileName), 
                )
                buffer = file.read().decode('unicode_escape')
                orders = EdiTalker.readBuffer( buffer )
                for order in orders:
                    orderDate = datetime.strptime(order['data']['time'], "%Y%m%d")
                    past = datetime.now() - timedelta(days=6)
                    if orderDate < past:
                        msg = "El pedido es demasiado antiguo (>6 días) "
                        _logger.error (f"Zacalog: EDI: {msg}")
                        EdiWriter.saveError(self.env, 201, order, msg)
                        #TODO: Delete from ftp
                        #ftp.remove(os.path.join(path, fileName))
                        raise Exception (msg)
                        
                    try:
                        EdiWriter.createSaleOrderFromEdi( self.env, order, file )
                        EdiWriter.deleteError(self.env, order)
                    except Exception as e: 
                        msg = "Zacalog: EDI: getOrdersFromSeres. Exception: " +str(e)
                        _logger.error (msg)
                        raise(e)
                        #self._getSlack().sendWarn( msg, "test2") #TODO:

                ftp.remove(os.path.join(path, fileName))

            except Exception as e:
                _logger.error (f"Zacalog: EDI: ftp: file {fileName} could not be retrieved: " + str(e))

    def send(self):
        pass #TODO: Generate and send all files to Seres