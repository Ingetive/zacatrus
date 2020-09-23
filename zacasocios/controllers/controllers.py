# -*- coding: utf-8 -*-
from odoo import http

# class Zacasocios(http.Controller):
#     @http.route('/zacasocios/zacasocios/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/zacasocios/zacasocios/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('zacasocios.listing', {
#             'root': '/zacasocios/zacasocios',
#             'objects': http.request.env['zacasocios.zacasocios'].search([]),
#         })

#     @http.route('/zacasocios/zacasocios/objects/<model("zacasocios.zacasocios"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('zacasocios.object', {
#             'object': obj
#         })