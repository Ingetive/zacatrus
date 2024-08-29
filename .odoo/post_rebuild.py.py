import os
from odoo import api, SUPERUSER_ID

def post_rebuild(cr, registry):
    # Obtener el entorno y la base de datos
    env = api.Environment(cr, SUPERUSER_ID, {})
    current_env = os.getenv('OE_ENV')

    # Modificar un parámetro de configuración
    env['ir.config_parameter'].set_param('zacatrus_base.magento_url', current_env+' https://dummy.zacatrus.es')

    # Puedes agregar más configuraciones según sea necesario
    # Guardar cambios
    cr.commit()

if __name__ == "__main__":
    # Llama a la función al ejecutar el script
    post_rebuild(cr, registry)
