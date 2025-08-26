from odoo import http
from odoo.http import request
from io import BytesIO
import barcode
from barcode.writer import SVGWriter
import xml.etree.ElementTree as ET

class BarcodeSVGController(http.Controller):

    @http.route('/edi/barcode/svg', type='http', auth='public')
    def barcode_svg(self, value=None, barcode_type='gs1_128', width=None, height=None):
        if not value:
            return request.make_response('Missing value', [('Content-Type', 'text/plain')])

        try:
            barcode_class = barcode.get_barcode_class(barcode_type)
            buffer = BytesIO()

            # Paramètres URL facultatifs : width et height (en mm)
            try:
                desired_width = float(width) if width else None
                desired_height = float(height) if height else 20.0  # défaut 20mm
            except ValueError:
                return request.make_response('Invalid width/height value', [('Content-Type', 'text/plain')])

            quiet_zone = 3.0  # mm

            # Estimation des modules nécessaires pour GS1-128
            estimated_modules = len(value) * 11

            # Calcul automatique du module_width si width est défini
            if desired_width:
                module_width = (desired_width - 2 * quiet_zone) / estimated_modules
            else:
                module_width = 0.3  # valeur par défaut

            writer_options = {
                'module_width': module_width,
                'module_height': desired_height,
                'quiet_zone': quiet_zone,
                'font_size': 12,
                'text_distance': 2,
                'write_text': False,
            }

            barcode_obj = barcode_class(value, writer=SVGWriter())
            barcode_obj.write(buffer, options=writer_options)

            svg_data = buffer.getvalue().decode('utf-8')
            root = ET.fromstring(svg_data)

            # Corriger le fond (rectangle 100% noir)
            for rect in root.findall('.//{http://www.w3.org/2000/svg}rect'):
                if rect.attrib.get('width') == '100%' and rect.attrib.get('height') == '100%':
                    rect.set('fill', 'white')  # Fond blanc

            final_svg = ET.tostring(root, encoding='utf-8', method='xml')

            return request.make_response(
                final_svg,
                headers=[('Content-Type', 'image/svg+xml')]
            )

        except Exception as e:
            return request.make_response(str(e), [('Content-Type', 'text/plain')])
