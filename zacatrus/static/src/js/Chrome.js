odoo.define('zacatrus.chrome', function (require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');

    const ZacatrusChrome = (Chrome) =>
        class extends Chrome {
            showCashMoveButton() {
                return this.env.pos && this.env.pos.config && this.env.pos.config.cash_control && this.env.pos.config.has_cash_move_permission;
            }
        };

    Registries.Component.extend(Chrome, ZacatrusChrome);

    return Chrome;
});
