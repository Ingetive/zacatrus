# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class PrintNodePrintJob(models.Model):
    """ PrintNode Job entity
    """

    _name = 'printnode.printjob'
    _description = 'PrintNode Job'

    printnode_id = fields.Float('Direct Print ID')
    printnode_copy_id = fields.Char("Direct Print ID copy", compute="_compute_printnode_copy_id", 
                                    store="True")

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        ondelete='cascade',
    )

    description = fields.Char(
        string='Label',
        size=64
    )
    
    @api.depends("printnode_id")
    def _compute_printnode_copy_id(self):
        for r in self:
            r.printnode_copy_id = r.printnode_id
            
