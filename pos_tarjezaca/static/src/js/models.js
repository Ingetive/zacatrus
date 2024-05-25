odoo.define("pos_tarjezaca.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var TarjezacaPayment = require("pos_tarjezaca.payment");
    models.register_payment_method("tarjezaca_payment", TarjezacaPayment);

    var _posmodelproto = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        after_load_server_data: function () {
            for (var payment_method_id in this.payment_methods) {
                var payment_method = this.payment_methods[payment_method_id];
                if (payment_method.use_payment_terminal == "tarjezaca_payment") {
                    this.config.use_proxy = false;
                }
            }
            return _posmodelproto.after_load_server_data.apply(this, arguments);
        },
    });

    var _paymentlineproto = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function () {
            _paymentlineproto.initialize.apply(this, arguments);
            // Id of the terminal transaction, used to find the payment
            // line corresponding to a terminal transaction status coming
            // from the terminal driver.
            this.terminal_transaction_id = null;
            // Success: null: in progress, false: failed: true: succeeded
            this.terminal_transaction_success = null;
            // Human readable transaction status, set if the transaction failed.
            this.terminal_transaction_status = null;
            // Additional information about the transaction status.
            this.terminal_transaction_status_details = null;
        },
        init_from_JSON: function (json) {
            _paymentlineproto.init_from_JSON.apply(this, arguments);
            this.terminal_transaction_id = json.terminal_transaction_id;
            this.terminal_transaction_success = json.terminal_transaction_success;
            this.terminal_transaction_status = json.terminal_transaction_status;
            this.terminal_transaction_status_details =
                json.terminal_transaction_status_details;
        },
        export_as_JSON: function () {
            var vals = _paymentlineproto.export_as_JSON.apply(this, arguments);
            vals.terminal_transaction_id = this.terminal_transaction_id;
            vals.terminal_transaction_success = this.terminal_transaction_success;
            vals.terminal_transaction_status_details = this.terminal_transaction_status_details;
            return vals;
        },
    });
});
