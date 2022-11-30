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
            var client = order.get_client();
            if (pay_line.amount < this.pos.config.x_min_amount){
                Gui.showPopup("ErrorPopup", {title: "Error", body: "Ops, el importe mínimo para financiar es "+this.pos.config.x_min_amount+" euros.",});
                return false;
            }
            if (!client || !client['email'] || client['email'] == ''){
                Gui.showPopup("ErrorPopup", {title: "Error", body: "Sorry, es necesario asignar un cliente con email al pedido.",});
                return false;   
            }
            var phone = false;
            if (client['mobile'] && client['mobile'] != ''){
                phone = client['mobile'];
            }
            else if (client['phone'] && client['phone'] != ''){
                phone = client['phone'];
            }
            var articles = [];
            for(var i = 0, len = orderlines.length; i < len; i++){
                if (orderlines[i].product){
                    articles.push({
                        'id': orderlines[i].product.id, 
                        'price': orderlines[i].get_price_with_tax(), 
                        'qty': orderlines[i].get_quantity(), 
                        'tax': orderlines[i].get_tax()
                    });
                }
            }
            var data = {
                "email": client['email'],
                "amount": pay_line.amount,
                "articles": articles
            };
            if (phone){
                data['phone'] = phone;
            }

            return rpc.query({
                model: 'pos.payment.method',
                method: 'aplazame',
                args: [this.pos.config.id, order.name, JSON.stringify(data)],
            })
            .then(function(ret){                            
                console.log("");
                if (!ret["ok"]) {
                    Gui.showPopup("ErrorPopup", {title: "Atención", body: ret["cause"],});
                }
                else {
                    return true;
                }
                return false;
            },function(type, err){
                Gui.showPopup("ErrorPopup", {title: "Error 20", body: "No puedo procesar el pago.",});
                return false;
            });
        },
    });
    return AplazamePayment;
});
