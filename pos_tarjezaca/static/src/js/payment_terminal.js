/*
    Copyright 2020 Akretion France (http://www.akretion.com/)
    @author: Alexis de Lattre <alexis.delattre@akretion.com>
    @author: Stéphane Bidoul <stephane.bidoul@acsone.eu>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("pos_tarjezaca.payment", function (require) {
    "use strict";

    var core = require("web.core");
    var PaymentInterface = require("point_of_sale.PaymentInterface");
    const {Gui} = require("point_of_sale.Gui");
    var rpc = require('web.rpc');

    var _t = core._t;

    var OCAPaymentTerminal = PaymentInterface.extend({
        init: function () {
            console.log("init payment terminal");
            this._super.apply(this, arguments);
        },

        send_payment_request: function () {
            console.log("Send payment");
            this._super.apply(this, arguments);
            return this._oca_payment_terminal_pay();
        },

        _oca_payment_terminal_pay: function () {
            var order = this.pos.get_order();
            var pay_line = order.selected_paymentline;
            var currency = this.pos.currency;
            if (pay_line.amount <= 0) {
                // TODO check if it's possible or not
                this._show_error(
                    _t("Cannot process transactions with zero or negative amount.")
                );
                return Promise.resolve();
            }

            var self = this;

            return Gui.showPopup('TextInputPopup', {
                   title: 'Pagar con Tarjezaca',
                   body: 'Introduce el código.',
                }).then(({ confirmed, payload: code }) => {
                        if (confirmed) {
                            console.log(code, 'payload')
                            console.log("We are going to redeem  "+ pay_line.amount +" from "+code+" card.");
                            
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
    return OCAPaymentTerminal;
});
