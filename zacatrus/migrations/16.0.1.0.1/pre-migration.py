# Copyright 2023 Factor Libre S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute(
        """
            delete from ir_ui_view where arch_fs ilike '%delivery_dhl_parcel%';
            delete from ir_ui_view where arch_fs ilike '%pos_ticket_without_price%';
            delete from ir_ui_view where arch_fs ilike '%stock_location_children%';
        """
    )
