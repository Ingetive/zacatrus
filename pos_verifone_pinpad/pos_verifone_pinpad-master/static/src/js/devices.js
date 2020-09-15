odoo.define('pos_verifone_pinpad.devices', function(require){
    "use strict";
    var core = require('web.core');
    var devices = require('point_of_sale.devices');
    devices.ProxyDevice.include({
        send_amount_pinpad: function(amount, cashier, order_name, payment_line_uid){
            var self = this;
            var ret = new $.Deferred();
            var function_name = '';
            if (amount > 0){
                function_name = 'set_amount_pinpad';
            }else{
                function_name = 'get_amount_pinpad';
            }
            this.message(function_name, {
                total_with_tax:Math.abs(amount),
                user:cashier,
                name:order_name,
                puerto:parseInt(this.pos.config.pinpad_port),
                cliente:parseInt(this.pos.config.pinpad_customer),
                tienda:parseInt(this.pos.config.pinpad_shop),
                tpv:parseInt(this.pos.config.pinpad_pos),
                pinpad_host:this.pos.config.pinpad_host,
                payment_line_uid:payment_line_uid
            }).then(function(result){
                ret.resolve(result);
            });
            return ret;
        }
    });
});