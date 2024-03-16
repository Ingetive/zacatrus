# Copyright 2023 Factor Libre S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):

    # Eliminar vistas de modulos no migrados
    cr.execute(
        """
            delete from ir_ui_view where arch_fs ilike '%delivery_dhl_parcel%';
            delete from ir_ui_view where arch_fs ilike '%pos_ticket_without_price%';
            delete from ir_ui_view where arch_fs ilike '%stock_location_children%';
        """
    )

    # Solucionar incidencia de error actualización printnode
    # 1. Añadir el campo report_id_v14 si aún no existe
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='printnode_scenario' AND column_name='report_id_v14') THEN
                ALTER TABLE printnode_scenario ADD COLUMN report_id_v14 integer;
            END IF;
        END
        $$;
    """)

    # 2. Copiar los valores de report_id a report_id_v14
    cr.execute("""
        UPDATE printnode_scenario SET report_id_v14 = report_id;
    """)

    # 3. Actualizar el valor de report_id a 29 en todos los registros
    cr.execute("""
        UPDATE printnode_scenario SET report_id = 29;
    """)