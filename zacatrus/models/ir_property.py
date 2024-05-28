# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Property(models.Model):
    _inherit = 'ir.property'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Property, self).create(vals_list)
        for record in res:
            if record.name == 'property_product_pricelist':
                record.sync_tarifa_companies()
        return res
    
    def write(self, vals):
        res = super(Property, self).write(vals)
        self.sync_tarifa_companies()
        return res
    
    def sync_tarifa_companies(self):
        if self.env.context.get('no_update_tarifa'):
            return
        
        for r in self:
            if r.name == 'property_product_pricelist':
                value_reference = r.value_reference
                    
                companies = self.env["res.company"].search([('id', '!=', r.company_id.id)])
                for company in companies:
                    property = self.env['ir.property'].sudo().search([
                        ('name', '=', r.name),
                        ('res_id', '=', r.res_id),
                        ('fields_id', '=', r.fields_id.id),
                        ('type', '=', 'many2one'),
                        ('company_id', '=', company.id)
                    ], limit=1)

                    if property:
                        if property.value_reference != value_reference:
                            property.with_context(no_update_tarifa=True).write({'value_reference': value_reference})
                    else:
                        self.env['ir.property'].sudo().create({
                            'name': r.name,
                            'res_id': r.res_id,
                            'company_id': company.id,
                            'type': 'many2one',
                            'fields_id': r.fields_id.id,
                            'value_reference': value_reference
                        }) 