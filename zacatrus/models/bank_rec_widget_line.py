# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, Command


class BankRecWidgetLine(models.Model):
    """
    Esta clase extiende el modelo 'bank.rec.widget.line' para personalizar la línea del widget de conciliación bancaria.
    """
    _inherit = "bank.rec.widget.line"

    @api.depends('flag')
    def _compute_source_aml_fields(self):
        """
        Sobrescribe el método _compute_source_aml_fields para incluir el valor de 'ref' en el 'source_aml_move_name'
        si el campo 'ref' del movimiento contable relacionado (source_aml_id.move_id) está presente.
        """
        # Ejecutar flujo estandar
        super(BankRecWidgetLine, self)._compute_source_aml_fields()

        # Asignar el valor de 'ref' a 'source_aml_move_name' si 'ref' está presente
        for line in self:
            if line.source_aml_move_id and line.source_aml_move_id.ref:
                line.source_aml_move_name = f"{line.source_aml_move_name} ({line.source_aml_move_id.ref})"