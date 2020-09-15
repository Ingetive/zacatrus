odoo.define('pos_verifone_pinpad.models', function(require){
    "use strict";
    var core = require('web.core');
    var _t = core._t;

    var models = require('point_of_sale.models');

    models.load_fields('pos.config', [
        'iface_pinpad_via_proxy',
        'pinpad_port',
        'pinpad_customer',
        'pinpad_shop',
        'pinpad_pos',
        'pinpad_host'
    ]);
    models.load_fields("account.journal", "verifone_pinpad_payment");

    var _pos_config = _.findWhere(
        models.PosModel.prototype.models,
        {model: "pos.config"}
    );

    var _pos_config_loaded = _pos_config.loaded;
    _pos_config.loaded = function (self, configs){
        _pos_config_loaded.apply(this, arguments);
        self.config.use_proxy = self.config.use_proxy || self.config.iface_pinpad_via_proxy;
    };

    var _paylineproto = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        init_from_JSON: function (json) {
            _paylineproto.init_from_JSON.apply(this, arguments);
            this.verifone_pending_payment = json.verifone_pending_payment;
            this.verifone_operation = json.verifone_operation;
            this.verifone_account = json.verifone_account;
            this.verifone_card_number = json.verifone_card_number;
            this.verifone_owner = json.verifone_owner;
            this.verifone_store = json.verifone_store;
            this.verifone_terminal = json.verifone_terminal;
            this.verifone_operation_number = json.verifone_operation_number;
            this.verifone_authorization_code = json.verifone_authorization_code;
            this.verifone_reading_type = json.verifone_reading_type;
            this.verifone_cvm = json.verifone_cvm;
            this.verifone_aid = json.verifone_aid;
            this.verifone_lbl = json.verifone_lbl;
            this.verifone_bin = json.verifone_bin;
            this.verifone_arc = json.verifone_arc;
        },
        export_as_JSON: function(){
            return _.extend(_paylineproto.export_as_JSON.apply(this, arguments), {
                verifone_pending_payment: this.verifone_pending_payment,
                verifone_operation: this.verifone_operation,
                verifone_account: this.verifone_account,
                verifone_card_number: this.verifone_card_number,
                verifone_owner: this.verifone_owner,
                verifone_store: this.verifone_store,
                verifone_terminal: this.verifone_terminal,
                verifone_operation_number: this.verifone_operation_number,
                verifone_authorization_code: this.verifone_authorization_code,
                verifone_reading_type: this.verifone_reading_type,
                verifone_cvm: this.verifone_cvm,
                verifone_aid: this.verifone_aid,
                verifone_lbl: this.verifone_lbl,
                verifone_bin: this.verifone_bin,
                verifone_arc: this.verifone_arc
            });
        },

        export_for_printing: function(){
            return {
                amount: this.get_amount(),
                journal: this.cashregister.journal_id[1],
                verifone_pending_payment: this.verifone_pending_payment,
                verifone_operation: this.verifone_operation,
                verifone_account: this.verifone_account,
                verifone_card_number: this.verifone_card_number,
                verifone_owner: this.verifone_owner,
                verifone_store: this.verifone_store,
                verifone_terminal: this.verifone_terminal,
                verifone_operation_number: this.verifone_operation_number,
                verifone_authorization_code: this.verifone_authorization_code,
                verifone_reading_type: this.verifone_reading_type,
                verifone_cvm: this.verifone_cvm,
                verifone_aid: this.verifone_aid,
                verifone_lbl: this.verifone_lbl,
                verifone_bin: this.verifone_bin,
                verifone_arc: this.verifone_arc
            };
        }
    });
});