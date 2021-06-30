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
            console.log("Tarjezaca clicked");
/*
            var self = this;
            const { confirmed, payload } = await this.showPopup('TextInputPopup', {
               title: this.env._t('Activar Tarjezaca'),
               body: this.env._t('Introduce el código.'),
            });
            if (confirmed) {
               console.log(payload, 'payload')
            }
*/
        }
    }

    TarjezacaSystem.template = 'Tarjezaca';

    ProductScreen.addControlButton({
        component: TarjezacaSystem,
        condition: function() {
            return true;
        },
    });

    console.log("registering Tarjezaca controls...");
    Registries.Component.add(TarjezacaSystem);

    return TarjezacaSystem;
});
