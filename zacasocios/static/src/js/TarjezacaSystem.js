odoo.define('zacasocios.TarjezacaSystem', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    //var models = require('point_of_sale.models');
    var core = require('web.core');
    var rpc = require('web.rpc');

    class TarjezacaSystem extends PosComponent {
        constructor() {
            super(...arguments);
            console.log("constructor Tarjezaca");
            useListener('click', this.onClick);
        }
        async onClick() {
        }
    }

    TarjezacaSystem.template = 'Tarjezaca';

    ProductScreen.addControlButton({
        component: Tarjezaca,
        condition: function() {
            return true;
        },
    });

    console.log("registering Tarjezaca controls...");
    Registries.Component.add(TarjezacaSystem);

    return TarjezacaSystem;
});
