/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(ControlButtons.prototype, {
    fichasID: false,
    clientId: false,
    addingPoints: false,
    setup() {
        super.setup();
        this.pos = usePos();
        
        setTimeout(() => {
            this.addFichasButton();
            this.checkClient();
        }, 1000);
    },

    checkClient() {
        var client = this.pos.get_order().get_partner();
        if (client && (!this.clientId || this.clientId != client.id)){
            this.clientId = client.id;
            this._getClientBalance();
        }
        setTimeout(() => {
            this.checkClient();
        }, 1000);
    },
    
    addFichasButton() {
        if (document.querySelector('#fichas_button')) {
            return;
        }
        
        const controlButtonsContainer = document.querySelector('.control-buttons') || 
                                      document.querySelector('.pos-control-buttons') ||
                                      document.querySelector('[class*="control"]');
        
        if (!controlButtonsContainer) {
            console.log("Conteneur des boutons de contrôle non trouvé");
            return;
        }
        
        // Créer le bouton Fichas
        const fichasButton = document.createElement('button');
        fichasButton.id = 'fichas_button';
        fichasButton.className = 'btn btn-light btn-lg control-button';
        fichasButton.innerHTML = `
            <i class="fa fa-gift me-2"></i>
            <span class="control-button-label">Fichas</span>
        `;
        fichasButton.addEventListener('click', () => this.clickFichas());
        
        controlButtonsContainer.appendChild(fichasButton);
    },
    
    async clickFichas() {
        const order = this.pos.get_order();
        
        if (!order) {
            this.dialog.add(AlertDialog, {
                title: _t("No Order"),
                body: _t("No order found. Please add products to the order first."),
            });
            return;
        }
        
        if (!document.querySelector('#fichas_button').textContent.includes("Quitar")){
            const total = order.get_total_with_tax();
            const fichas = Math.floor(total / 10);
            
            if (fichas === 0) {
                this.dialog.add(AlertDialog, {
                    title: _t("Insufficient Amount"),
                    body: _t(`Total: ${total}€\nMinimum: 10€ for 1 ficha`),
                });
                return;
            }
            this.addFichasToOrder();
        }
        else {
            this.removeFichasFromOrder();
        }
    },

    async _getFichasProductId() {
        if (!this.fichasID) {
            try {
                const orm = this.env.services.orm;
                const fichasProductId = await orm.call(
                    'zacasocios.zacasocios',
                    'getFichasProductId',
                    []
                );
                if (fichasProductId) {
                    this.fichasID = fichasProductId;
                }
            } catch (error) {
                console.error("Error getting fichas product id:", error);
                this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("Error getting fichas product ID."),
                });
            }
        }
        return this.fichasID;
    },
    async addFichasToOrder (  ) {
        if (!this.addingPoints && this.fichasID){

            var order = this.pos.get_order();
            var selected_orderline = order.get_selected_orderline();
            if (!order.get_orderlines().length) {
                console.log("no order lines.")
                return;
            }
            if (this.addingPoints){ 
                console.log("already adding lines.")
            }
            else{
                this.addingPoints = true;
                var orderlines = order.get_orderlines();
                var val = this._calculateNumberOfFichas( );
                var modified = false;
                for(var i = 0, len = orderlines.length; i < len; i++){
                    if (orderlines[i].product && orderlines[i].product.id == this.fichasID){
                        orderlines[i].set_quantity(-1*val);
                        modified = true;
                    }
                }
                if (this.fichas && this.fichas >= 100 && !modified){
                    let fichasProduct = this.pos.models["product.product"].getBy("id", this.fichasID);
                    
                     try {
                        const newLine = await this.pos.addLineToCurrentOrder(
                            {product_id: fichasProduct}, 
                            {}, 
                            false
                        );
                        newLine.set_quantity(-1*val);
                        
                        newLine.is_fichas_line = true;
                        newLine.fichas_protected = true;
                        
                        this.protectFichasLines();
                            
                        const button = document.querySelector('#fichas_button');
                        if (button) {
                            button.innerHTML = '<i class="fa fa-gift me-2"></i><span class="control-button-label">Quitar</span>';
                        }
                         
                     } catch (error) {
                         this.dialog.add(AlertDialog, {
                             title: _t("Error"),
                             body: _t("No se pudo agregar las fichas al pedido."),
                         });
                         console.error("Error adding fichas to order:", error);
                     }
                }
                else {
                    this.dialog.add(AlertDialog, {
                        title: _t("Error"),
                        body: _t("No hay fichas disponibles."),
                    });
                    console.log("no fichas to add.");
                }
                this.addingPoints = false;
                
            }
        }
    },

    protectFichasLines() {
        const order = this.pos.get_order();
        if (!order) return;
        
        const orderlines = order.get_orderlines();
        orderlines.forEach(line => {
            if (line.product_id && line.product_id.id == this.fichasID) {
                const originalSetQuantity = line.set_quantity;
                line.set_quantity = function(qty) {
                    if (this.is_fichas_line) {
                        return false;
                    }
                    return originalSetQuantity.call(this, qty);
                };
                
                const originalSetUnitPrice = line.set_unit_price;
                line.set_unit_price = function(price) {
                    if (this.is_fichas_line) {
                        return false;
                    }
                    return originalSetUnitPrice.call(this, price);
                };
            }
        });
    },

    removeFichasFromOrder() {
        const order = this.pos.get_order();
        if (!order) {
            console.log("No order found");
            return;
        }
        
        const orderlines = order.get_orderlines();
        let fichasRemoved = false;
        
        for (let i = orderlines.length - 1; i >= 0; i--) {
            const line = orderlines[i];
            if (line.product_id && line.product_id.id == this.fichasID) {
                order.removeOrderline(line);
                fichasRemoved = true;
            }
        }
        
        if (fichasRemoved) {
            this._setText();
        } else {
            console.log("Zacalog: no fichas found to remove");
        }
    },
    
    
    forceUIUpdate() {
        try {
            // Forcer la mise à jour de l'interface POS
            if (this.pos && this.pos.trigger) {
                this.pos.trigger('update');
            }
            
            // Déclencher un événement personnalisé
            const event = new CustomEvent('fichasAdded', {
                detail: { count: 1 }
            });
            document.dispatchEvent(event);
            
        } catch (error) {
            console.log("Error forcing UI update:", error);
        }
    },
    
    updateOrderTotal(order) {
        try {
            const lines = order.get_orderlines();
            let total = 0.0;
            
            lines.forEach(line => {
                if (line.get_total_with_tax) {
                    total += line.get_total_with_tax();
                }
            });
            
            // Mettre à jour le total
            if (order.set_total_with_tax) {
                order.set_total_with_tax(total);
            } else {
                order.amount_total = total;
            }
            
        } catch (error) {
            console.error("Error updating order total:", error);
        }
    },

    _fichasApplied( ) {
        if (this.fichasID){
            var order = this.pos.get_order();
            var orderlines = order.get_orderlines();
            for(var i = 0, len = orderlines.length; i < len; i++){
                const line = orderlines[i];
                if (line.product_id && line.product_id.id == this.fichasID){
                    return true;
                }
            }
        }
        return false;
    },

    _calculateNumberOfFichas(  ){
        if (this.fichasID){
            var order = this.pos.get_order();
            var total     = order ? order.get_total_with_tax() : 0;
            var orderlines = order.get_orderlines();
            for(var i = 0, len = orderlines.length; i < len; i++){
                 if (orderlines[i].product && orderlines[i].product.id == this.fichasID){
                    total = total - orderlines[i].get_price_with_tax();
                }
            }

            var ret = 0;

            if (this.fichas){
                ret = this.fichas;
                if (ret > total*100 / 2)
                    ret = total*100 /2;

                ret = parseInt(ret / 100) * 100;
            }

            return ret;
        }
    },
    _setText(){
        if (! this._fichasApplied()){
            if (this.fichas && this.fichas > 0){         
                var available = this._calculateNumberOfFichas();
                 const button = document.querySelector('#fichas_button');
                 if (button) {
                    button.innerHTML = '<i class="fa fa-gift me-2"></i>' +
                        '<span class="control-button-label">' + available + ' F.</span>';
                 }
            }
            else {
                const button = document.querySelector('#fichas_button');
                if (button) {
                    button.innerHTML = '<i class="fa fa-gift me-2"></i>' +
                        '<span class="control-button-label">Fichas</span>';
                }
            }
        }
        else {
            const button = document.querySelector('#fichas_button');
            if (button) {
                button.innerHTML = '<i class="fa fa-gift me-2"></i>' +
                    '<span class="control-button-label">Quitar</span>';
            }
        }
    },

    async _getClientBalance(  ) {
        if (! this.fichasID){
            await this._getFichasProductId();
        }

        var order = this.pos.get_order();
        var client = order.get_partner();

        //order.set_pricelist(client.pricelist_id);

        this.fichas = false;
        if (client != null){
            this.zacasocio = false;
            if (client && client.property_product_pricelist && client.property_product_pricelist.id == 3){
                this.zacasocio = true;
                if (!client.email){
                    this.dialog.add(AlertDialog, {
                        title: _t("Cliente inválido"),
                        body: _t("El cliente no tiene un email asignado."),
                    });
                } else {
                    const orm = this.env.services.orm;
                    //const fichasProductId = await orm.call(
                    try {
                        const _fichas = await orm.call(
                            'zacasocios.zacasocios',
                            'getBalance',
                            [client.email, this.pos.config.name]
                        )
                        this.fichas =  Math.floor(_fichas);
                        //core.bus.trigger('got_fichas', this.fichas);
                        this._setText();
                    } catch (error) {
                        this.dialog.add(AlertDialog, {
                            title: _t("Error"),
                            body: _t("Error al obtener las fichas del cliente."),
                        });
                    }
                }            
            }
            else{
                this.fichas = 0;
                console.log("No es zacasocio.");
            }
        }
        else {
            console.log("No client.");
        }
    }
});
