/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ControlButtons.prototype, {
    fichasID: false,
    setup() {
        super.setup();
        // Ajouter le bouton Fichas après l'initialisation
        setTimeout(() => {
            this.addFichasButton();
        }, 1000);
    },
    
    addFichasButton() {
        // Vérifier si le bouton existe déjà
        if (document.querySelector('#fichas_button')) {
            return;
        }
        
        // Chercher le conteneur des boutons de contrôle
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
        
        // Ajouter l'événement de clic
        fichasButton.addEventListener('click', () => this.clickFichas());
        
        // Ajouter le bouton au conteneur
        controlButtonsContainer.appendChild(fichasButton);
        
        console.log("Bouton Fichas ajouté à l'interface");
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
        
        const total = order.get_total_with_tax();
        const fichas = Math.floor(total / 10);
        
        if (fichas === 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Insufficient Amount"),
                body: _t(`Total: ${total}€\nMinimum: 10€ for 1 ficha`),
            });
            return;
        }
        
        // Demander confirmation
        this.dialog.add(AlertDialog, {
            title: _t("Add Fichas"),
            body: _t(`Add ${fichas} fichas to the order?\n\nTotal: ${total}€\nFichas: ${fichas}`),
            confirm: () => this.addFichasToOrder(fichas),
        });
    },

    async _getFichasProductId() {
        if (!this.fichasID) {
            console.log("getting fichas product id...");
            try {
                // Utiliser le service ORM moderne
                const orm = this.env.services.orm;
                const fichasProductId = await orm.call(
                    'zacasocios.zacasocios',
                    'getFichasProductId',
                    []
                );
                
                console.log("Got fichas id:", fichasProductId);
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
    },
    
    async addFichasToOrder(fichasCount) {
        const order = this.pos.get_order();

        if (!this.fichasID){
            await this._getFichasProductId();
        }
        
        try {
            let fichasProduct = null;
            
            if (this.pos.models && this.pos.models["product.product"]) {
                const products = this.pos.models["product.product"].records;
                fichasProduct = Object.values(products).find(product => 
                    product.id == this.fichasID
                );
                console.log("fichasProduct:", fichasProduct);
            }
            
            // Méthode 2: Chercher dans la configuration POS
            if (!fichasProduct && this.pos.config && this.pos.config.available_product_ids) {
                const availableProducts = this.pos.config.available_product_ids;
                fichasProduct = availableProducts.find(product => 
                    product.id == this.fichasID
                );
            }
            
            // Méthode 3: Utiliser un produit existant comme base
            if (!fichasProduct) {
                console.log("Produit 'Fichas' non trouvé, utilisation d'une approche alternative");
                
                // Essayer d'utiliser le premier produit disponible comme base
                if (this.pos.models && this.pos.models["product.product"]) {
                    const products = this.pos.models["product.product"].records;
                    const firstProduct = Object.values(products)[0];
                    if (firstProduct) {
                        fichasProduct = {
                            ...firstProduct,
                            id: this.fichasID,
                            name: 'Fichas',
                            display_name: 'Fichas',
                            price: 0.0,
                            lst_price: 0.0,
                            is_fichas: true
                        };
                    }
                }
                
                // Si toujours pas de produit, créer une ligne manuellement
                if (!fichasProduct) {
                    console.log("Création d'une ligne de fichas manuelle");
                    this.addFichasLineManually(order, fichasCount);
                    return;
                }
            }
            
            console.log("Produit Fichas trouvé:", fichasProduct);
            
            // Supprimer les fichas existantes (remettre à zéro)
            order._fichas_count = 0;
            order._fichas_display = null;
            
            // Utiliser la méthode manuelle pour éviter les erreurs de taxes_id
            this.addFichasLineManually(order, fichasCount);
            
        } catch (error) {
            console.error("Error adding fichas:", error);
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Error adding fichas to the order."),
            });
        }
    },
    
    addFichasLineManually(order, fichasCount) {
        try {
            console.log("Ajout manuel de fichas à la commande");
            
            // Stocker les fichas dans un champ personnalisé de la commande
            if (!order._fichas_count) {
                order._fichas_count = 0;
            }
            order._fichas_count += fichasCount;
            
            // Ajouter un champ personnalisé pour l'affichage
            order._fichas_display = `${order._fichas_count} fichas`;
            
            // Mettre à jour le total de la commande (sans ajouter de ligne)
            this.updateOrderTotal(order);
            
            // Forcer la mise à jour de l'interface
            this.forceUIUpdate();
            
            // Message de succès
            this.dialog.add(AlertDialog, {
                title: _t("Success"),
                body: _t(`${fichasCount} fichas added to the order!\n\nTotal fichas: ${order._fichas_count}`),
            });
            
        } catch (error) {
            console.error("Error adding fichas manually:", error);
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Error adding fichas to the order."),
            });
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
            // Recalculer le total de la commande (sans les fichas)
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
            
            console.log("Total de la commande mis à jour:", total);
            console.log("Fichas dans la commande:", order._fichas_count || 0);
            
        } catch (error) {
            console.error("Error updating order total:", error);
        }
    }
});
