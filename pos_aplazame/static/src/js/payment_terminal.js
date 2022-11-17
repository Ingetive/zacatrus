odoo.define("pos_aplazame.payment", function (require) {
    "use strict";

    var core = require("web.core");
    var PaymentInterface = require("point_of_sale.PaymentInterface");
    const {Gui} = require("point_of_sale.Gui");
    var rpc = require('web.rpc');

    var _t = core._t;

    var AplazamePayment = PaymentInterface.extend({
        init: function () {
            console.log("init payment terminal");
            this._super.apply(this, arguments);
        },

        send_payment_request: function () {
            console.log("Send payment");
            this._super.apply(this, arguments);
            return this._aplazame_pay();
        },

        _aplazame_pay: function() { 
            var order = this.pos.get_order();
            var pay_line = order.selected_paymentline;
            var orderlines = order.get_orderlines();
            console.log( order.name );
            console.log(JSON.stringify(this.pos.config.id));
            console.log(JSON.stringify(this.pos.config.name));
            console.log(JSON.stringify(this.pos.config.x_min_amount));
            //console.log(JSON.stringify(this.pos.config));
            console.log(JSON.stringify(order));
            console.log(JSON.stringify(orderlines));
            console.log("pay_line.amount: "+ pay_line.amount);
            if (pay_line.amount < this.pos.config.x_min_amount){
                Gui.showPopup("ErrorPopup", {title: "Error", body: "Ops, el importe mínimo para financiar es "+this.pos.config.x_min_amount+" euros.",});
                return false;
            }
            //TODO: Check client with email
            for(var i = 0, len = orderlines.length; i < len; i++){
                if (orderlines[i].product){
                    console.log("product id: "+ orderlines[i].product.id);
                }
            }

            return rpc.query({
                model: 'pos.payment.method',
                method: 'aplazame',
                args: [this.pos.config.id, order.name],
            })
            .then(function(ret){                            
                console.log("");
                if (!ret["ok"]) {
                    Gui.showPopup("ErrorPopup", {title: "Error", body: ret["cause"],});
                }
                else {
                    return true;
                }
                return false;
            },function(type, err){
                Gui.showPopup("ErrorPopup", {title: "Error 20 ", body: "No puedo procesar el pago.",});
                return false;
            });
        },

        _show_error: function (msg, title) {
            Gui.showPopup("ErrorPopup", {
                title: title || _t("Payment Terminal Error"),
                body: msg,
            });
        },
    });
    return AplazamePayment;
});
