import base64, os
from odoo import models, fields, api
import paramiko
from .EdiTalker import EdiTalker
from .EdiWriter import EdiWriter

class BundleWizard(models.TransientModel):
    _name = 'zacaedi.bundle'
    #_inherit = 'zacaedi.bundle'

    name = fields.Char(string='name')
    order_ids = fields.Many2many('sale.order', string='Pedidos')
    file = fields.Binary("CSV file")

    url = fields.Char("Dowload link", compute="_compute_url")
    def _compute_url(self):
        for record in self:
            record.url = '/web/content/zacaedi.bundle/%s/file/%s?download=true' % (self.id, "orders.csv")
    
    def generateCSV(self):
        print("Zacalog: EDI: Generate CSV")

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
                print("EdiTalker: Cannot connect to sftp.")
        except Exception as err:
            raise Exception(err)
    
    @api.model
    def getAllPendingOrders(self):
        path = '/recepcion/orders_d96a'

        fileList = BundleWizard._getFtp(self.env).listdir( path )
        ret = []

        print("Zacalog: EDI: getting files...")
        for fileName in fileList:
            print(f"Zacalog: EDI: getting {fileName}...")
            #fileName = file.split('/')[3]
            ret.append(fileName)
            try:
                file = BundleWizard._getFtp(self.env).file(
                    os.path.join(path, fileName), 
                )
                buffer = file.read().decode("utf-8")
                orders = EdiTalker.readBuffer( buffer )
                for order in orders:
                    print("ORDER")
                    print(order['data']['orderNumber'])
                    try:
                        orderId = EdiWriter.createSaleOrderFromEdi( self.env, order, file )
                    except Exception as e: 
                        msg = "Zacalog: EDI: getOrdersFromSeres. Exception: " +str(e)
                        print (msg)
                        raise(e)
                        #self._getSlack().sendWarn( msg, "test2") #TODO:

                #TODO: if deleteFromFTP:
                #    self.deleteFile(file)

            except Exception as e:
                print (f"Zacalog: EDI: ftp: file {fileName} could not be retrieved.")

