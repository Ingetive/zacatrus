from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.model
    def create(self, vals):
        notification = super(MailNotification, self).create(vals)
        partnersConfig = self.env['ir.config_parameter'].sudo().get_param('zacatrus_base.block_partner_ids')
        if partnersConfig:
            partners = [int(i) for i in partnersConfig.split(",")]
            #partners = [3, 50]
            #_logger.warning(f"Zacalog: MailNotification: {partners}")
            #vals: {'notification_status': 'ready', 'mail_message_id': 620, 'notification_type': 'inbox', 'mail_mail_id': False, 'sms_id': False, 'res_partner_id': 3, 'sms_number': False, 'is_read': False, 'read_date': False, 'failure_type': False, 'failure_reason': False}

            #_logger.warning(f"Zacalog: MailNotification: user id: {notification.res_partner_id} {notification.notification_type} {notification.mail_message_id}")

            if vals['res_partner_id'] in partners:
                if vals['notification_type'] != 'inbox':
                    _logger.warning(f"Zacalog: MailNotification: bloqueado: no es interno.")
                    notification.unlink()
                else:
                    args = [
                        '|',
                        '|',
                        ('subject', 'like', 'Ha sido asignado'),
                        ('subject', 'like', 'Vous avez été assigné'),
                        ('subject', 'like', 'You have been assigned'),                    
                        ('id', '=', vals['mail_message_id'])
                    ]
                    count =  self.env['mail.message'].search_read(args)
                    if count:
                        _logger.warning(f"Zacalog: MailNotification: bloqueado uno de 'asignado a'.")
                        notification.unlink()

        return notification