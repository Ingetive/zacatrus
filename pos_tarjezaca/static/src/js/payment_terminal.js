odoo.define("pos_tarjezaca.payment", function (require) {
    "use strict";

    var core = require("web.core");
    var PaymentInterface = require("point_of_sale.PaymentInterface");
    const {Gui} = require("point_of_sale.Gui");
    var rpc = require('web.rpc');

    var _t = core._t;

    var TarjezacaPayment = PaymentInterface.extend({
        init: function () {
            console.log("init payment terminal");
            this._super.apply(this, arguments);
        },

        send_payment_request: function () {
            console.log("Send payment");
            this._super.apply(this, arguments);
            return this._tarjezaca_pay();
        },

        _tarjezaca_pay: function () {
            var order = this.pos.get_order();
            var pay_line = order.selected_paymentline;
            var currency = this.pos.currency;
            if (pay_line.amount <= 0) {
                // TODO check if it's possible or not
                this._show_error(
                    _t("No podemos procesar pagos con importe negativo.")
                );
                return Promise.resolve();
            }

            var self = this;

            return Gui.showPopup('TextInputPopup', {
                   title: 'Pagar con Tarjezaca',
                   body: 'Introduce el código.',
                }).then(({ confirmed, payload: code }) => {
                        if (confirmed) {
                            console.log("Zacalog: We are going to redeem  "+ pay_line.amount +" from "+code+" card.");
                            
                            return rpc.query({
                                model: 'ir.config_parameter',
                                method: 'search_read',
                                args: [[['key', '=', 'zacatrus_base.card_product_id']], ['key', 'value']],
                            })
                            .then(function(ret){
                                console.log(JSON.stringify(ret));
                                if (ret.length != 1){
                                    Gui.showPopup("ErrorPopup", {title: "Error", body: "Error de conexión. Por favor, inténtalo más tarde.",});
                                    return false;
                                }
                                var cardId = ret[0]['value']
                                var orderlines = order.get_orderlines();
                                for(var i = 0, len = orderlines.length; i < len; i++){
                                    if (orderlines[i].product && orderlines[i].product.id == cardId){
                                        Gui.showPopup("ErrorPopup", {title: "Error", body: "No podemos pagar una tarjeta regalo con otra tarjeta regalo.",});
                                        return Promise.resolve();
                                    }
                                }
                                return rpc.query({
                                    model: 'pos.payment.method',
                                    method: 'redeem',
                                    args: [code, pay_line.amount],
                                })
                                .then(function(ret){                            
                                    console.log("redeem done: "+JSON.stringify(ret));
                                    if (!ret["ok"]) {
                                        Gui.showPopup("ErrorPopup", {title: "Error", body: ret["cause"],});
                                    }
                                    else {
                                        return true;
                                    }
                                    return false;
                                },function(type, err){
                                    Gui.showPopup("ErrorPopup", {title: "Error 20 ", body: "No puedo canjear esa tarjezaca.",});
                                    return false;
                                });
                            });
                        }
                        else {
                            return false;
                        }
                    }
                );
        },
        _show_error: function (msg, title) {
            Gui.showPopup("ErrorPopup", {
                title: title || _t("Payment Terminal Error"),
                body: msg,
            });
        },
    });
    return TarjezacaPayment;
});
