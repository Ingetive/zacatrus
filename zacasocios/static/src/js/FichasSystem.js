//const FICHAS_BARCODE = "100001";
const TARIFA_ZACASOCIOS = 3;

odoo.define('zacasocios.FichasSystem', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    //var models = require('point_of_sale.models');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var addingPoints = false;
    var fichas = false;
    var hooksSet = false;
    var zacasocio = false;
    var pendingUpdate = false;
    var fichasID = false;

    class FichasSystem extends PosComponent {
        constructor() {
            super(...arguments);
            console.log("constructor FichasSystem");
            useListener('click', this.onClick);
        }
        mounted() {
            console.log("mounted");
            this._getClientBalance();
            if (!hooksSet){                
                this.env.pos.on('change:selectedClient', () => {
                    console.log("change:selectedClient");
                    var client = this.env.pos.get_order().get_client();
                    fichas = false;

                    console.log("change client. zacasocio: "+zacasocio);

                    this._removeFichasFromOrder();
                    this._getClientBalance();
                    this._setText();
                });
                this.env.pos.on('change:selectedOrder', () => {
                    console.log("change:selectedOrder");
                    //this._getClientBalance();
                    //this._setText();
                });
                
                this.env.pos.get_order().orderlines.on('change', this._onChange, this);
                core.bus.on('got_fichas', this, this._onGotFichas);
                core.bus.on('got_fichas_product_id', this, this._onGotId);

                hooksSet = true;
            }
        }

        _onGotId(){
            console.log("got id")
            this._getClientBalance();
        }

        _onGotFichas(_fichas){
            console.log("got fichas :"+ _fichas)
            this._setText()
        }
        _setText(){
            if (! this._fichasApplied()){
                if (fichas && fichas > 0){         
                    console.log("_setText: setting values");  
                    var available = this._calculateNumberOfFichas();
                    var suffix = " ("+available + " de "+fichas+")";
                    if (this.el && this.el.querySelector)
                        this.el.querySelector('#fichas_button').textContent = "Canjear Fichas" +suffix;
                }
                else {
                    if (this.el && this.el.querySelector)
                        this.el.querySelector('#fichas_button').textContent = "Canjear Fichas";
                }
            }
            else {
                console.log("_setText: fichas applied");
            }
        }

        _onChange(){
            this._setText();
            if (this._fichasApplied()){
                this._addFichasToOrder();
            }
        }
        willUnmount() {
            console.log("willUnmount");
            if (fichasID){
                var order = this.env.pos.get_order();
                var orderlines = order.get_orderlines();
                var max = this._calculateNumberOfFichas( );
                var current = 0;
                for(var i = 0, len = orderlines.length; i < len; i++){
                    if (orderlines[i].product && orderlines[i].product.id == fichasID){
                        current = (-1)*orderlines[i].get_quantity();
                    }
                }
                console.log("current:"+current);
                console.log("max:"+max);
                if (current > max && max > 0){
                    this._addFichasToOrder();
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Fichas'),
                        body: this.env._t(
                            "OJO: Error en el conteo de Fichas. Por favor, recalcula."
                        ),
                    });
                    throw "Cálculo de Fichas no válido.";
                }
                //this._addFichasToOrder();
                this.env.pos.off('change:selectedClient', null, this);
                this.env.pos.off('change:selectedOrder', null, this);
            }
        }
        async onClick() {
            var order = this.env.pos.get_order();
            
            if (this.el.querySelector('#fichas_button').textContent.includes("Canjear")){
                var client = order.get_client();
                if (client == null){
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Fichas'),
                        body: this.env._t(
                            "No hay cliente seleccionado."
                        ),
                    });
                }
                else{
                    console.log("zacasocio: "+zacasocio);
                    if (!zacasocio){
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Fichas'),
                            body: this.env._t(
                                "OJO, este cliente no está marcado como zacasocio."
                            ),
                        });
                    }
                    else {
                        if (fichas === 0){
                            this._getClientBalance();
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Fichas'),
                                body: this.env._t(
                                    "Sin saldo suficiente o no es la primera compra de hoy."
                                ),
                            });
                        }
                        else {
                            if (!fichas){
                                this._getClientBalance();
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('Fichas'),
                                    body: this.env._t(
                                        "Cargando. Por favor, prueba otra vez."
                                    ),
                                });
                            }
                            else {
                                this.el.querySelector('#fichas_button').textContent = "Quitar Fichas";
                                this._addFichasToOrder ();
                            }
                        }
                    }
                }
            }
            else  {
                console.log("Quitar");
                this._removeFichasFromOrder ();
                this._setText();
            }
        }
        _addFichasToOrder (  ) {
            if (!this.addingPoints && fichasID){

                var order = this.env.pos.get_order();
                var selected_orderline = order.get_selected_orderline();
                if (!order.get_orderlines().length) {
                    console.log("no order lines.")
                    return;
                }
                if (addingPoints){
                    console.log("already adding lines.")
                }
                else{
                    console.log("adding points line")
                    this.addingPoints = true;
                    var orderlines = order.get_orderlines();
                    var val = this._calculateNumberOfFichas( );
                    var modified = false;
                    for(var i = 0, len = orderlines.length; i < len; i++){
                        if (orderlines[i].product && orderlines[i].product.id == fichasID){
                            orderlines[i].set_quantity(-1*val);
                            modified = true;
                        }
                    }
                    if (fichas && fichas >= 100 && !modified){
                        var fichasProduct = this.env.pos.db.get_product_by_id(fichasID); //get_product_by_id
                        console.log( { quantity: val } );
                        console.log( { fichasProduct } );
                        order.add_product(fichasProduct, { quantity: -1*val });
                        this.el.querySelector('#fichas_button').textContent = "Quitar Fichas";
                        console.log( "---" );
                    }
                    this.addingPoints = false;
                    
                }
            }
        }
        _fichasApplied (  ) {
            if (fichasID){
                var order = this.env.pos.get_order();
                var orderlines = order.get_orderlines();
                for(var i = 0, len = orderlines.length; i < len; i++){
                    if (orderlines[i].product && orderlines[i].product.id == fichasID){
                        return orderlines[i].get_quantity() != 0;
                    }
                }
            }
            return false;
        }
        _removeFichasFromOrder (  ) {
            if (fichasID){
                var order = this.env.pos.get_order();
                var selected_orderline = order.get_selected_orderline();
                if (!order.get_orderlines().length) {
                    console.log("no order lines.")
                    return;
                }
                if (!addingPoints){
                    console.log("already adding lines.")
                    this.addingPoints = true;
                    var orderlines = order.get_orderlines();
                    for(var i = 0, len = orderlines.length; i < len; i++){
                        if (orderlines[i].product && orderlines[i].product.id == fichasID){
                            orderlines[i].set_quantity(0);
                            //orderlines.remove(orderlines[i]);
                        }
                    }
                    this.addingPoints = false;
                }
            }
        }
        _calculateNumberOfFichas(  ){
            if (fichasID){
                var order = this.env.pos.get_order();
                var total     = order ? order.get_total_with_tax() : 0;
                var orderlines = order.get_orderlines();
                for(var i = 0, len = orderlines.length; i < len; i++){
                    if (orderlines[i].product && orderlines[i].product.id == fichasID){
                        total = total - orderlines[i].get_price_with_tax();
                    }
                }

                var ret = 0;

                if (fichas){
                    ret = fichas;
                    if (ret > total*100 / 2)
                        ret = total*100 /2;

                    ret = parseInt(ret / 100) * 100;
                }

                console.log("calculateNumberOfFichas, ret="+ret);

                return ret;
            }
        }
        _getClientBalance(  ) {
            if (! fichasID){
                this._getFichasProductId()
            }
            else {
                var order = this.env.pos.get_order();
                var client = order.get_client();

                //order.set_pricelist(client.pricelist_id);

                fichas = false;
                if (client != null){
                    zacasocio = false;
                    if (client && client.property_product_pricelist[0] == TARIFA_ZACASOCIOS){
                        zacasocio = true;
                        console.log(client.property_product_pricelist[0]);
                    }
                    if (zacasocio){
                        console.log("getting Fichas...");
                        rpc.query({
                            model: 'zacasocios.zacasocios',
                            method: 'getBalance',
                            args: [client.email, this.env.pos.config.name],
                        })
                        .then(function(_fichas){
                            if (! fichas){
                                fichas =  Math.floor(_fichas);
                                core.bus.trigger('got_fichas', fichas);
                                console.log("_getClientBalance: Got "+fichas+" fichas.");
                            }
                            else {
                                console.log("Already gone for fichas.");
                            }
                        },function(type,err){
                            alert("Error 10: No puedo obtener las fichas de este cliente.");
                        });
                    }
                    else{
                        fichas = 0;
                        console.log("No es zacasocio.");
                    }
                }
            }
        }
        _getFichasProductId( ) {
            if (!fichasID){
                console.log("getting fichas product id...");
                rpc.query({
                    model: 'zacasocios.zacasocios',
                    method: 'getFichasProductId',
                    args: [],
                })
                .then(function(fichasProductId){
                    console.log("Got fichas id.");
                    if (fichasProductId){
                        fichasID = fichasProductId;
                        core.bus.trigger('got_fichas_product_id', fichas);
                    }
                },function(type,err){
                    alert("Error 20: No puedo obtener el id de product de fichas.");
                });
            }
        }
    }
    FichasSystem.template = 'Fichas';

    ProductScreen.addControlButton({
        component: FichasSystem,
        condition: function() {
            return true;
        },
    });

    console.log("registering FichasSystem");
    Registries.Component.add(FichasSystem);

    return FichasSystem;
});
