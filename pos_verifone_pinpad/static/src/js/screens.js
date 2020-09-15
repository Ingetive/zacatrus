odoo.define('pos_verifone_pinpad.screens', function(require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var screens = require('point_of_sale.screens');
    var framework = require('web.framework');
    var PaymentScreenWidget = screens.PaymentScreenWidget;

    PaymentScreenWidget.include({
        render_paymentlines: function() {
            this._super.apply(this, arguments);
            var self = this;
            var lines = this.pos.get_order().get_paymentlines();
        },
        click_paymentline_pinpad: function(cid, modelo, options) {
            var queue = this.pos.proxy_queue;
            var self = this;
            var order = this.pos.get_order();
            var lines = order.get_paymentlines();
            var paid = false;
            console.log('enviando a la cola');
            queue.schedule(function() {
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i].verifone_pending_payment === true && lines[i].verifone_pending_payment !== false) {
                        console.log('tiene pinpad');
                        var amount = lines[i].amount;
                        framework.blockUI();
                        var cashier = null;
                        if (self.pos.cashier) {
                            cashier = self.pos.cashier.name_shop;
                        } else {
                            cashier = 'CAJERO';
                        }
                        var for_ = i;
                        self.pos.proxy.send_amount_pinpad(amount, cashier, order.uid, lines[i].cid).then(function(response) {
                            if(response.code === '0'){
                                console.log('response');
                                var paid = false;
                                for (var a = 0; a < lines.length; a++ ) {
                                    paid = true;
                                    if(lines[a].cid == response.payment_line_uid){
                                        lines[a].verifone_pending_payment = false;
                                        lines[a].verifone_operation = response.operation;
                                        lines[a].verifone_account = response.account;
                                        lines[a].verifone_card_number = response.credit_card;
                                        lines[a].verifone_owner = response.owner;
                                        lines[a].verifone_store = response.store;
                                        lines[a].verifone_terminal = response.terminal;
                                        lines[a].verifone_operation_number = response.operation_number;
                                        lines[a].verifone_authorization_code = response.authorization_code;
                                        lines[a].verifone_reading_type = response.reading_type;
                                        lines[a].verifone_cvm = response.cvm;
                                        lines[a].verifone_aid = response.aid;
                                        lines[a].verifone_lbl = response.lbl;
                                        lines[a].verifone_bin = response.bin;
                                        lines[a].verifone_arc = response.arc;
                                    }
                                }
                                for (var b = 0; b < lines.length; b++ ) {
                                if(lines[b].verifone_pending_payment && lines[b].verifone_pending_payment !== false){
                                    paid = false;
                                }
                                }
                                if(paid){
                                framework.unblockUI();
                                self.validate_order.call(self, options);
                                }
                            } else {
                                if (typeof(response.error) !== 'undefined') {
                                    framework.unblockUI();
                                    if(!self.$('.next').is(":visible")){
                                        self.$('.next').show()
                                    }
                                    self.gui.show_popup('error', {
                                        'title': _t('Error'),
                                        'body': response.error
                                    });
                                }else{
                                    framework.unblockUI();
                                    if(!self.$('.next').is(":visible")){
                                        self.$('.next').show()
                                    }
                                    self.gui.show_popup('error', {
                                        'title': _t('Error'),
                                        'body': response
                                    });
                                }
                            }
                            self.reset_input();
                            self.render_paymentlines();
                        });
                    }
                }
                return;
            }, { duration: 10000, repeat: false });
        },
        click_paymentmethods: function(id) {
            var i;
            var order = this.pos.get_order();
            var cashregister = null;
            for (i = 0; i < this.pos.cashregisters.length; i++) {
                if (this.pos.cashregisters[i].journal_id[0] === id) {
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }
            if (this.pos.config.iface_pinpad_via_proxy && cashregister.journal.verifone_pinpad_payment) {
                var already_swipe_pending = false;
                var lines = order.get_paymentlines();

                if (already_swipe_pending) {
                    this.gui.show_popup('error', {
                        'title': _t('Error'),
                        'body': _t('One credit card swipe already pending.'),
                    });
                } else {
                    this._super(id);
                    order.selected_paymentline.verifone_pending_payment = true;
                    this.render_paymentlines();
                    order.trigger('change', order); // needed so that export_to_JSON gets triggered
                }
            } else {
                this._super(id);
            }
        },
        validate_order: function(options) {
            var self  = this;
            var pinpad = false;
            var paid = true;
            var payment_line = self.pos.get_order().paymentlines.models;
            var order = self.pos.get_order();
            for ( var i = 0; i < payment_line.length; i++ ) {
                if(payment_line[i].cashregister.journal.verifone_pinpad_payment){
                    pinpad = true;
                }
            }
            for (var b = 0; b < payment_line.length; b++ ) {
                if(payment_line[b].verifone_pending_payment && payment_line[b].verifone_pending_payment !== false){
                    paid = false;
                }
            }
            if(order.is_paid()){
                if(paid || !pinpad){
                    this._super(options);
                }else{
                    self.click_paymentline_pinpad($(this).data('cid'), this, options);
                }
            }
        },
        click_delete_paymentline: function(cid) {
            var self = this;
            var lines = this.pos.get_order().get_paymentlines();

            for (var i = 0; i < lines.length; i++) {
                if (lines[i].cid === cid && !lines[i].verifone_pending_payment && !lines[i].verifone_pending_payment ==='undefined') {
                    self.gui.show_popup('error', {
                        'title': _t('Error'),
                        'body': _t('Is not possible to delete an already processed credit card payment')
                    });
                    return;
                }
            }

            this._super(cid);
        },
    });
});