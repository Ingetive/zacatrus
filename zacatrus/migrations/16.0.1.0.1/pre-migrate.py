from odoo.upgrade import util

def migrate(cr, version):
    util.uninstall_module(cr, 'stock_generate_putaway_from_inventory')