import base64, os, logging
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
            record.url = '/web/content/zacaedi.bundle/%s/file/%s?download=true' % (self.id, "orders.csv")
    
    def generateCSV(self):
        data = "Your text goes here"
        self.file = base64.b64encode(data.encode())

        return {
            'name': 'Cerrar albaranes EDI y generar CSV',
            'view_mode': 'form',    
            'res_model': 'zacaedi.bundle',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }
    
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
        orders =  self.env['sale.order'].search_read([('x_edi_status', '=', EdiWriter.EDI_STATUS_INIT)], order="id desc", limit=1)
        orderList = []
        for order in orders:
            orderList.append( (4, [order['id']]) )

        #Errors to show
        errors =  self.env['zacaedi.error'].search_read([('bundle_id', '=', currentBundle['id'])])
        error_msgs = ""
        for error in errors:
            error_msgs += f"{error['message']}\n"

        currentBundle.write({'error_msgs':error_msgs})

        return {
            'name': 'Enviar albaranes EDI y generar CSV',
            "type" : "ir.actions.act_window",
            "res_model" : self._name,
            "view_mode": "form", 
            "res_id": currentBundle['id'],
            "action": "edi_bundle_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {'tal': 'cual'}
        }
    
    @api.model
    def getAllPendingOrders(self):
        path = self.env['ir.config_parameter'].sudo().get_param('zacaedi.inputpath') #'/lamp0/web/vhosts/estasjugando.com/recepcion/orders_d96a'

        fileList = BundleWizard._getFtp(self.env).listdir( path )
        ret = []

        for fileName in fileList:
            _logger.info(f"Zacalog: EDI: getting {fileName}...")
            #fileName = file.split('/')[3]
            ret.append(fileName)
            try:
                file = BundleWizard._getFtp(self.env).file(
                    os.path.join(path, fileName), 
                )
                buffer = file.read().decode("utf-8")
                orders = EdiTalker.readBuffer( buffer )
                for order in orders:
                    try:
                        order = EdiWriter.createSaleOrderFromEdi( self.env, order, file )
                    except Exception as e: 
                        msg = "Zacalog: EDI: getOrdersFromSeres. Exception: " +str(e)
                        _logger.error (msg)
                        raise(e)
                        #self._getSlack().sendWarn( msg, "test2") #TODO:

                #TODO: if deleteFromFTP:
                #    self.deleteFile(file)

            except Exception as e:
                _logger.error (f"Zacalog: EDI: ftp: file {fileName} could not be retrieved.")

