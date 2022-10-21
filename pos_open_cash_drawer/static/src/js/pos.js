odoo.define('pos_open_cash_drawer', function (require) {
"use strict";

const { useListener } = require('web.custom_hooks');
const ProductScreen = require('point_of_sale.ProductScreen');
const Registries = require('point_of_sale.Registries');

    const PosResProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener('click-open-cashbox', this._openCashDrawer);
            }

            async _openCashDrawer() {            	
                this.env.pos.proxy.printer.open_cashbox();
            }
        }

    Registries.Component.extend(ProductScreen, PosResProductScreen);
});

