odoo.define("pos_paylands.payment", function (require) {
    "use strict";

    var core = require("web.core");
    var PaymentInterface = require("point_of_sale.PaymentInterface");
    const {Gui} = require("point_of_sale.Gui");
    var rpc = require('web.rpc');

    var _t = core._t;

    var PaylandsPayment = PaymentInterface.extend({
        init: function () {
            this._super.apply(this, arguments);
        },

        send_payment_request: function () {
            this._super.apply(this, arguments);
            return this._paylands_pay();
        },
        send_payment_cancel: function (order, cid) {
            this._super.apply(this, arguments);
            return this._paylands_cancel(false);
        },
        close: function () {
            this._super.apply(this, arguments);
        },

        _paylands_cancel: function (ignore_error) {
            var self = this;
            var config = this.pos.config;

            return rpc.query({
                model: 'pos.payment.method',
                method: 'cancel',
                args: [this.pos.config.id, this.pos.get_order().name],
            }, {
                timeout: 5000,
                shadow: true,
            }).then(function (status) {
                self.was_cancelled = true;
                Gui.showPopup("ErrorPopup", {title: "Paylands", body: _t('Por favor, cancélalo en el datáfono.'),});   
            }).catch(function (status) {
                Gui.showPopup("ErrorPopup", {title: "Paylands error", body: _t('Error de conexión.'),});
            })
        },


        _reset_state: function () {
            this.was_cancelled = false;
            this.remaining_polls = 4;
            clearTimeout(this.polling);
        },


        _paylands_get_sale_id: function () {
            var config = this.pos.config;
            return _.str.sprintf('%s (ID: %s)', config.display_name, config.id);
        },

        _poll_for_response: function (resolve, reject) {
            var self = this;

            if (this.was_cancelled) {
                resolve(false);
                return Promise.resolve();
            }

            return rpc.query({
                model: 'pos.payment.method',
                method: 'get_status',
                args: [this.pos.config.id, this.pos.get_order().name],
            }, {
                timeout: 5000,
                shadow: true,
            }).catch(function (data) {
                if (self.remaining_polls != 0) {
                    self.remaining_polls--;
                } else {
                    reject();
                    self.poll_error_order = self.pos.get_order();
                    return self._handle_odoo_connection_failure(data);
                }
                // This is to make sure that if 'data' is not an instance of Error (i.e. timeout error),
                // this promise don't resolve -- that is, it doesn't go to the 'then' clause.
                return Promise.reject(data);
            }).then(function (res) {
                console.log("status: "+res['status']);
                //var notification = status.latest_response;                
                var order = self.pos.get_order();
                var line = self.pending_paylands_line() || resolve(false);

                if (res['status'] != 0) {
                    //var response = notification.SaleToPOIResponse.PaymentResponse.Response;
                    //var additional_response = new URLSearchParams(response.AdditionalResponse);

                    if (res['status'] == 200) {
                        var config = self.pos.config;
                        // var payment_response = notification.SaleToPOIResponse.PaymentResponse;
                        //var payment_result = payment_response.PaymentResult;

                        /*
                        var cashier_receipt = payment_response.PaymentReceipt.find(function (receipt) {
                            return receipt.DocumentQualifier == 'CashierReceipt';
                        });
                        */

                        //if (cashier_receipt) {
                            //line.set_cashier_receipt("THIS is a test");
                            line.set_receipt_info( res['additional']['ticket_footer'] );
                        //}


/*
                        var customer_receipt = payment_response.PaymentReceipt.find(function (receipt) {
                            return receipt.DocumentQualifier == 'CustomerReceipt';
                        });
                        if (customer_receipt) {
                            line.set_receipt_info(self._convert_receipt_info(customer_receipt.OutputContent.OutputText));
                        }
*//*
                        var tip_amount = payment_result.AmountsResp.TipAmount;
                        if (config.paylands_ask_customer_for_tip && tip_amount > 0) {
                            order.set_tip(tip_amount);
                            line.set_amount(payment_result.AmountsResp.AuthorizedAmount);
                        }*/

                        //TODO: Poner datos de la transaccion pnp
                        line.transaction_id = res['additional']['uuid'];
                        line.card_type = res['additional']['brand'];
                        //line.cardholder_name = additional_response.get('cardHolderName') || '';
                        
                        resolve(true);
                    }
                    else if (res['status'] >= 500) { 
                        //var message = additional_response.get('message');
                        Gui.showPopup("ErrorPopup", {title: "Paylands", body: _t('Denegada...'),});

                        line.set_payment_status('retry');
                        reject();
                    }
                    else if (res['status'] == 300) { 
                        //var message = additional_response.get('message');
                        Gui.showPopup("ErrorPopup", {title: "Paylands", body: _t('Cancelado por el usuario'),});

                        line.set_payment_status('retry');
                        reject();
                    }
                    else {
                        // TODO:
                        /*
                        var message = additional_response.get('message');
                        self._show_error(_.str.sprintf(_t('Message from Paylands: %s'), message));

                        // this means the transaction was cancelled by pressing the cancel button on the device
                        if (message.startsWith('108 ')) {
                            resolve(false);
                        } else {
                            line.set_payment_status('retry');
                            reject();
                        }
                        */
                    }
                } else {
                    line.set_payment_status('waitingCard')
                }
            });
        },

        start_get_status_polling: function () {
            var self = this;
            var res = new Promise(function (resolve, reject) {
                // clear previous intervals just in case, otherwise
                // it'll run forever
                clearTimeout(self.polling);
                self._poll_for_response(resolve, reject);
                self.polling = setInterval(function () {
                    self._poll_for_response(resolve, reject);
                }, 5500);
            });

            // make sure to stop polling when we're done
            res.finally(function () {
                self._reset_state();
            });

            return res;
        },


        pending_paylands_line() {
            var line = this.pos.get_order().paymentlines.find(
            paymentLine => paymentLine.payment_method.use_payment_terminal === 'paylands_payment' && (!paymentLine.is_done()));
            //console.log("PAYMENT TERMINAL: "+line.payment_method.use_payment_terminal);
            return line;
        },

        _paylands_handle_response: function (response) {
            var line = this.pending_paylands_line();

            if (response.error && response.error.status_code == 401) {
                Gui.showPopup("ErrorPopup", {title: "Paylands error", body: _t('Authentication failed. Please check your Paylands credentials.'),});
                line.set_payment_status('force_done');
                return Promise.resolve();
            }

            response = response.SaleToPOIRequest;
            if (response && response.EventNotification && response.EventNotification.EventToNotify == 'Reject') {
                console.error('error from Paylands', response);

                var msg = '';
                if (response.EventNotification) {
                    var params = new URLSearchParams(response.EventNotification.EventDetails);
                    msg = params.get('message');
                }

                Gui.showPopup("ErrorPopup", {title: "Paylands error", body: msg,});
                if (line) {
                    line.set_payment_status('force_done');
                }

                return Promise.resolve();
            } else {
                line.set_payment_status('waitingCard');
                return this.start_get_status_polling();
            }
        },

        _doSend( code ){
            var self = this;
            var order = this.pos.get_order();
            var pay_line = order.selected_paymentline;
            var client = order.get_client();
            var clientId = 'anonymous';
            if (client){
                console.log(client);
                clientId = client.id;  
            }
            console.log("Send payment 2");
            var data = {
                "client": clientId,
                "amount": pay_line.amount,
                "order": code
                //"articles": articles
            };

            return rpc.query({
                model: 'pos.payment.method',
                method: 'paylands',
                args: [this.pos.config.id, order.name, JSON.stringify(data)],
            })
            .then(function(ret){
                console.log(ret);
                if (!ret['ok']) {
                    Gui.showPopup("ErrorPopup", {title: "Error "+ret['code'], body: ret['message'],});
                    return false;    
                }
                return self._paylands_handle_response(data);
            },function(type, err){
                Gui.showPopup("ErrorPopup", {title: "Error 20", body: "No puedo procesar el pago.",});
                return false;
            });
            return false;
        },

        _paylands_pay: function() { 
            var order = this.pos.get_order();
            var pay_line = order.selected_paymentline;


            if (pay_line.amount > 0){
                return this._doSend( false );
            }
            else {
                return Gui.showPopup('TextInputPopup', {
                   title: 'Número de pedido (Order) original',
                   body: 'Ej.: 00001-051-0001.',
                }).then(({ confirmed, payload: code }) => {
                    if (code){
                        console.log("return: "+code);
                        return this._doSend(code);
                    }
                });
            }
            return false;

        },
    });
    return PaylandsPayment;
});
