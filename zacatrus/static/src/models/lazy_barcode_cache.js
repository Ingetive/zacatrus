/** @odoo-module **/

import LazyBarcodeCache from '@stock_barcode/lazy_barcode_cache';
import { patch } from 'web.utils';

patch(LazyBarcodeCache.prototype, 'zacatrus', {
    /**
     * @override
     */
    async getRecordByBarcode(barcode, model = false, onlyInCache = false, filters = {}) {
        let record = await this._super(barcode, model, onlyInCache, filters);

        if (record.size < 1) {
            // Considerar como valido el barcode menos el ultimo caracter
            const partialBarcode = barcode.slice(0, -1);

            // Obtener todos los modelos posibles de busqueda barcorde dado que model es false
            const models = Object.keys(this.dbBarcodeCache);

            // Iterar cada los modelos que tenga codigo de barras omitiendo el picking
            for (const m of models) {

                // TODO: Podria cambiar condicion para que solo permita los de product.product
                if (m == 'stock.picking') {
                    continue;
                }

                // Ajuste de estructura de datos para facilitar la busqueda
                const records = Object.values(this.dbBarcodeCache[m]).flat();

                // Buscar en el todos los registros del modelo de turno si corresponde algun registro en el barcode
                const recordId = records.find(id => {
                    const rec = this.getRecord(m, id);
                    return rec.barcode && rec.barcode.startsWith(partialBarcode);
                });

                // Construir respuesta siempre y cuando se identifique un ID valido de un producto
                if (recordId && m == 'product.product') {
                    const foundRecord = this.getRecord(m, recordId);
                    record = new Map([[m, {
                        id: foundRecord.id,
                        barcode: foundRecord.barcode,
                        default_code: foundRecord.default_code,
                        categ_id: foundRecord.categ_id,
                        code: foundRecord.code,
                        detailed_type: foundRecord.detailed_type,
                        tracking: foundRecord.tracking,
                        display_name: foundRecord.display_name,
                        uom_id: foundRecord.uom_id,
                    }]]);
                    break;
                }
            }
        }

        return record;
    },
});