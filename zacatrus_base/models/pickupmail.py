from odoo import models, fields, api
import logging, json, requests
from .zconta import Zconta 

_logger = logging.getLogger(__name__)

class PickupMail(models.Model):
    _name = 'zacatrus_base.pickupmail'
    _description = 'Mail to say that the order is ready to pickup.'

    order_id = fields.Char()
    name = fields.Char()
    email = fields.Char()
    url = fields.Char()
    address = fields.Char()

    def send(self):
        #template_id = 18 #self.env.ref('modulo.nombre_de_la_plantilla').id
        template = self.env.ref('zacatrus_base.pickup_order_ready')
        #template = self.env['mail.template'].browse(template_id)
        #template.email_to = self.email
        # self.id se refiere al ID del registro actual de este modelo
        template.send_mail(self.id, force_send=True)
