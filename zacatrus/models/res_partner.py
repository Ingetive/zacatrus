# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    x_partner_id8 = fields.Char("Id. en Odoo 8")
    
    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if 'property_product_pricelist' in vals:
            res.actualizar_tarifa_companias()
        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)
        if 'property_product_pricelist' in vals:
            self.actualizar_tarifa_companias()
        return res
    
    def actualizar_tarifa_companias(self):
        current_company = self.env.company
        for r in self:
            properties = self.env["ir.property"].sudo().search([
                ('name', '=', 'property_product_pricelist'),
                ('res_id', '=', "res.partner,%s" % r.id),
                ('company_id', '!=', current_company.id)
            ])
            
            value_reference = None
            if r.property_product_pricelist:
                value_reference = "product.pricelist,%s" % r.property_product_pricelist.id
                
            if properties:
                properties.write({'value_reference': value_reference})
            else:
                companies = self.env["res.company"].search([('id', '!=', current_company.id)])
                for company in companies:
                    self.env['ir.property'].sudo().create({
                        'name': 'property_product_pricelist',
                        'res_id': "res.partner,%s" % r.id,
                        'company_id': company.id,
                        'type': 'many2one',
                        'fields_id': self.env['ir.model.fields']._get_ids(r._name)['property_product_pricelist'],
                        'value_reference': value_reference
                    })
        
