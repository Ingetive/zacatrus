odoo.define('zacasocios.screens', function (require) {
"use strict";
// This file contains the Screens definitions. Screens are the
// content of the right pane of the pos, containing the main functionalities. 
//
// Screens must be defined and named in chrome.js before use.
//
// Screens transitions are controlled by the Gui.
//  gui.set_startup_screen() sets the screen displayed at startup
//  gui.set_default_screen() sets the screen displayed for new orders
//  gui.show_screen() shows a screen
//  gui.back() goes to the previous screen
//
// Screen state is saved in the order. When a new order is selected,
// a screen is displayed based on the state previously saved in the order.
// this is also done in the Gui with:
//  gui.show_saved_screen()
//
// All screens inherit from ScreenWidget. The only addition from the base widgets
// are show() and hide() which shows and hides the screen but are also used to 
// bind and unbind actions on widgets and devices. The gui guarantees
// that only one screen is shown at the same time and that show() is called after all
// hide()s
//
// Each Screens must be independant from each other, and should have no 
// persistent state outside the models. Screen state variables are reset at
// each screen display. A screen can be called with parameters, which are
// to be used for the duration of the screen only. 


var screens = require('point_of_sale.screens');
var rpc = require('web.rpc');

var fichas = false;
var workInProgress = false;
const FICHAS_BARCODE = "100001";
var m_order = false;
var m_db = false;

/* function removeFichas(order) {
    var orderlines = order.get_orderlines();

    for(var i = 0, len = orderlines.length; i < len; i++){
        if (orderlines[i].product && orderlines[i].product.barcode == FICHAS_BARCODE){
            order.orderline_remove( orderlines[i] );
        }
    }
}
*/

function getClientBalance( order, posName ) {
    m_order = order;
    var client = order.get_client();

    //order.set_pricelist(client.pricelist_id);

    fichas = false;
    if (client != null){
        workInProgress = true;
        // alert("Client is: "+ client.name)
        // alert("Client e)mail is: "+ client.email)
        // Ok, let's go for Fichas

        rpc.query({
                model: 'zacasocios.zacasocios',
                method: 'getBalance',
                args: [client.email, posName],
            })
            .then(function(_fichas){
                //self.saved_client_details(partner_id);
                fichas = _fichas;
                //alert("Found "+ fichas + " Fichas");
                addFichasToOrder( m_order );
                workInProgress = false;
            },function(type,err){
                workInProgress = false;
                var error_body = 'Your Internet connection is probably down.';
                if (err.data) {
                    var except = err.data;
                    error_body = except.arguments && except.arguments[0] || except.message || error_body;
                }
                alert( "Error 10: No puedo obtener las fichas de este cliente." );
            });
    }
}

var addingPoints = false;
function addFichasToOrder ( order ) {
    addingPoints = true;
    var orderlines = order.get_orderlines();
    var val = calculateNumberOfFichas( order);
    var modified = false;
    for(var i = 0, len = orderlines.length; i < len; i++){
        if (orderlines[i].product && orderlines[i].product.barcode == FICHAS_BARCODE){
            //order.remove_orderline(orderlines[i]);
            //order.select_orderline(orderlines[i]);
            orderlines[i].set_quantity(-1*val);
            modified = true;
        }
    }
    if (fichas && fichas >= 100 && !modified){
        var fichasProduct = m_db.get_product_by_barcode(FICHAS_BARCODE);
        //order.add_product(fichasProduct, { quantity: -1*val });
    }
    addingPoints = false;
}

function calculateNumberOfFichas( order ){
    var total     = order ? order.get_total_with_tax() : 0;
    var orderlines = order.get_orderlines();
    for(var i = 0, len = orderlines.length; i < len; i++){
        if (orderlines[i].product && orderlines[i].product.barcode == FICHAS_BARCODE){
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

screens.ClientListScreenWidget.include({
    save_changes: function(){
        m_db = this.pos.db;
        var order = this.pos.get_order();
        if( this.has_client_changed() ){
            var default_fiscal_position_id = _.findWhere(this.pos.fiscal_positions, {'id': this.pos.config.default_fiscal_position_id[0]});
            if ( this.new_client && this.new_client.property_account_position_id ) {
                var client_fiscal_position_id = _.findWhere(this.pos.fiscal_positions, {'id': this.new_client.property_account_position_id[0]});
                order.fiscal_position = client_fiscal_position_id || default_fiscal_position_id;
            } else {
                order.fiscal_position = default_fiscal_position_id;
                //order.set_pricelist(this.pos.default_pricelist);
            }
            if (this.new_client)
                order.set_pricelist(_.findWhere(this.pos.pricelists, {'id': this.new_client.property_product_pricelist[0]}) || this.pos.default_pricelist);
            else
                order.set_pricelist(this.pos.default_pricelist);

            order.set_client(this.new_client);
                    
            getClientBalance( order, this.pos.config.name );
        }
    }
});


screens.OrderWidget.include({
    update_summary: function(){
        var order = this.pos.get_order();
        var client = order.get_client();
        if (client == null){
            fichas = false;
        }

        if (!order.get_orderlines().length) {
            return;
        }

        var total     = order ? order.get_total_with_tax() : 0;
        var taxes     = order ? total - order.get_total_without_tax() : 0;

        this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
        this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);

        m_db = this.pos.db;
        var selected_orderline = order.get_selected_orderline();
        if (!addingPoints){
            if(!selected_orderline || selected_orderline.product.barcode  != FICHAS_BARCODE){
                addFichasToOrder ( order );
            }
        }
    }
});

screens.ScreenWidget.include({
    barcode_client_action: function(code){
        var partner = this.pos.db.get_partner_by_barcode(code.code);
        if(partner){
            this.pos.get_order().set_client(partner);
            this.pos.get_order().set_pricelist(_.findWhere(this.pos.pricelists, {'id': partner.property_product_pricelist[0]}) || this.pos.default_pricelist);
            getClientBalance(this.pos.get_order(), this.pos.config.name);
            return true;
        }
        this.barcode_error_action(code);
        return false;
    }
});


function setBalance( email, qty ) {
    rpc.query({
            model: 'zacasocios.zacasocios',
            method: 'setBalance',
            args: [email, qty, "[Odoo] Canjeadas en tienda"],
        })
        .then(function(){
            //alert("Substracted "+ qty + " Fichas")
        },function(type,err){
            var error_body = 'Your Internet connection is probably down.';
            if (err.data) {
                var except = err.data;
                error_body = except.arguments && except.arguments[0] || except.message || error_body;
            }
            alert( "Error 20. No puedo restarle las fichas a este cliente." );
        });
}

function earnByOrder( email, orderInfo ) {
    console.log(JSON.stringify(orderInfo));
    rpc.query({
            model: 'zacasocios.zacasocios',
            method: 'earnByOrder',
            args: [email, JSON.stringify(orderInfo)],
        })
        .then(function(){
            //alert("Fichas added")
        },function(type,err){
            var error_body = 'Your Internet connection is probably down.';
            if (err.data) {
                var except = err.data;
                error_body = except.arguments && except.arguments[0] || except.message || error_body;
                alert(error_body);
            }
            else {
                alert( "Error 30. No puedo añadirle fichas a este cliente." );
            }
        });
}

screens.PaymentScreenWidget.include({
    validate_order: function(force_validation) {
        if (this.order_is_valid(force_validation)) {
            /* Zacatrus */
            var order = this.pos.get_order()
            var client = order.get_client();
            var orderlines = order.get_orderlines();

            var orderInfo = [];
            for(var i = 0, len = orderlines.length; i < len; i++){
                if (orderlines[i].product && orderlines[i].product.barcode == FICHAS_BARCODE){
                    if (client != null){
                        setBalance(client.email, orderlines[i].get_quantity());
                    }
                }
                else {
                    var orderInfoLine = {"barcode": orderlines[i].product.barcode, "quantity": orderlines[i].get_quantity()};
                    orderInfo.push(orderInfoLine);
                }
            }
            if (client != null){
                earnByOrder(client.email, orderInfo);
            }
            /* / Zacatrus */

            this.finalize_validation();
        }
    }
});



});