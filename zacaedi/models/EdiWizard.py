from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class EdiWizard(models.Model):
    def _getDefaultModelAndId(self):
        return ("", 0)

    @api.model
    def notify(self, model, resId, msg, subject = "Error EDI"):
        #_logger.warning("Zacalog: EDI: Sending notification.")
        (model, resId) = self._getDefaultModelAndId()
            
        usersConfig = self.env['ir.config_parameter'].sudo().get_param('zacaedi.notify_user_ids')
        if usersConfig:
            userIds = [int(i) for i in usersConfig.split(",")]
            args = [
                ('model', '=', model),
                ('res_id', '=', resId),
                ('body', '=', msg),
            ]
            count =  self.env['mail.message'].search_count(args)
            if count == 0:
                #49 -> Sergio; 2 -> Mitchell Admin (local)
                args = [('id', 'in', userIds)]
                users = self.env['res.users'].search( args )
                partner_ids =  [(4, user.partner_id.id) for user in users]

                message = self.env['mail.message'].create({
                    'subject': subject,
                    'model': model,               # Modelo relacionado
                    'res_id': resId,                  # ID del registro relacionado
                    'body': msg,                    # Cuerpo del mensaje
                    'message_type': 'notification',     # Tipo de mensaje (comment, notification, etc.)
                    #'subtype_id': self.env.ref('mail.mt_automation').id,  # Subtipo del mensaje
                    'partner_ids':  partner_ids,
                })

                for user in users:
                    self.env['mail.notification'].create({
                        'mail_message_id': message.id,
                        'res_partner_id': user.partner_id.id,
                        'notification_type': 'inbox',  # Tipo de notificación (inbox, email, etc.)
                        'notification_status': 'ready',  # Estado de la notificación (ready, sent, etc.)
                    })