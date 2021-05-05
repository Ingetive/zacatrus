# -*- coding: utf-8 -*-
# from odoo import http


# class Zacatrus(http.Controller):
#     @http.route('/zacatrus/zacatrus/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/zacatrus/zacatrus/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('zacatrus.listing', {
#             'root': '/zacatrus/zacatrus',
#             'objects': http.request.env['zacatrus.zacatrus'].search([]),
#         })

#     @http.route('/zacatrus/zacatrus/objects/<model("zacatrus.zacatrus"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('zacatrus.object', {
#             'object': obj
#         })
