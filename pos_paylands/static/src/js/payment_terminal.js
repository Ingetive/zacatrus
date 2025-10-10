/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class PaylandsPayment extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.was_cancelled = false;
        this.remaining_polls = 4;
        this.polling = null;
    }

    async send_payment_request(uuid) {
        await super.send_payment_request(...arguments);
        const line = this.pos.get_order().get_selected_paymentline();
        line.set_payment_status("waiting");
        try {
            return await this._paylands_pay();
        } catch (error) {
            console.error(error);
            this._showError(String(error));
            return false;
        }
    }

    async send_payment_cancel(order, uuid) {
        super.send_payment_cancel(...arguments);
        const line = this.pos.get_order().get_selected_paymentline();
        const paylandsCancel = await this._paylands_cancel(false);
        if (paylandsCancel) {
            line.set_payment_status("retry");
            return true;
        }
    }

    async _paylands_cancel(ignore_error) {
        try {
            const status = await this.pos.data.silentCall(
                'pos.payment.method',
                'cancel',
                [this.pos.config.id, this.pos.get_order().name]
            );
            this.was_cancelled = true;
            this._showError(_t('Por favor, cancélalo en el datáfono.'), "Paylands");
            return status;
        } catch (error) {
            this._showError(_t('Error de conexión.'), "Paylands error");
            return false;
        }
    }

    _reset_state() {
        this.was_cancelled = false;
        this.remaining_polls = 4;
        clearTimeout(this.polling);
    }

    async _poll_for_response(resolve, reject) {
        if (this.was_cancelled) {
            resolve(false);
            return;
        }

        try {
            const res = await this.pos.data.silentCall(
                'pos.payment.method',
                'get_status',
                [this.pos.config.id, this.pos.get_order().name]
            );

            console.log("get_status -> status: " + res['status']);
            const order = this.pos.get_order();
            const line = this.pending_paylands_line();

            if (!line) {
                resolve(false);
                return;
            }

            if (res['status'] !== 0) {
                if (res['status'] === 200) {
                    line.set_receipt_info(res['additional']['ticket_footer']);
                    line.transaction_id = res['additional']['uuid'];
                    line.card_type = res['additional']['brand'];
                    resolve(true);
                } else if (res['status'] >= 500 && res['status'] < 600) {
                    this._showError(_t('Denegada.'), "Paylands");
                    line.set_payment_status('retry');
                    reject();
                } else if (res['status'] === 300) {
                    this._showError(_t('Cancelado por el usuario'), "Paylands");
                    line.set_payment_status('retry');
                    reject();
                } else {
                    this._showError(res['message'], "Paylands");
                    line.set_payment_status('retry');
                    reject();
                }
            } else {
                line.set_payment_status('waitingCard');
            }
        } catch (error) {
            if (this.remaining_polls !== 0) {
                this.remaining_polls--;
            } else {
                reject();
                this.poll_error_order = this.pos.get_order();
                this._showError(_t('Error de conexión con Paylands.'), "Paylands error");
                return;
            }
            console.error("Error polling for response:", error);
        }
    }

    start_get_status_polling() {
        return new Promise((resolve, reject) => {
            clearTimeout(this.polling);
            this._poll_for_response(resolve, reject);
            this.polling = setInterval(() => {
                this._poll_for_response(resolve, reject);
            }, 5500);
        }).finally(() => {
            this._reset_state();
        });
    }

    pending_paylands_line() {
        const order = this.pos.get_order();
        if (!order) return null;
        return order.paymentlines.find(
            paymentLine => paymentLine.payment_method.use_payment_terminal === 'paylands_payment' && (!paymentLine.is_done())
        );
    }

    async _paylands_handle_response(response) {
        const line = this.pending_paylands_line();

        if (response.error && response.error.status_code === 401) {
            this._showError(_t('Authentication failed. Please check your Paylands credentials.'), "Paylands error");
            if (line) line.set_payment_status('force_done');
            return Promise.resolve();
        }

        if (response && response.SaleToPOIRequest && response.SaleToPOIRequest.EventNotification && response.SaleToPOIRequest.EventNotification.EventToNotify === 'Reject') {
            console.error('error from Paylands', response);
            let msg = '';
            if (response.SaleToPOIRequest.EventNotification) {
                const params = new URLSearchParams(response.SaleToPOIRequest.EventNotification.EventDetails);
                msg = params.get('message');
            }
            this._showError(msg, "Paylands error");
            if (line) line.set_payment_status('force_done');
            return Promise.resolve();
        } else {
            if (line) line.set_payment_status('waitingCard');
            return this.start_get_status_polling();
        }
    }

    async _doSend(code) {
        const order = this.pos.get_order();
        const pay_line = order.get_selected_paymentline();
        
        if (!pay_line) {
            this._showError(_t("No payment line selected"), "Paylands Error");
            return false;
        }
        
        const client = order.partner;
        const clientId = client ? client.id : 'anonymous';

        const data = {
            "client": clientId,
            "amount": pay_line.amount,
            "order": code
        };

        try {
            const ret = await this.pos.data.silentCall(
                'pos.payment.method',
                'paylands',
                [this.pos.config.id, order.name, JSON.stringify(data)]
            );

            if (!ret['ok']) {
                this._showError(ret['message'], `Error ${ret['code']}`);
                return false;
            }
            return await this._paylands_handle_response(data);
        } catch (error) {
            this._showError(_t("No puedo procesar el pago."), "Error 20");
            console.error("Error in _doSend:", error);
            return false;
        }
    }

    async _paylands_pay() {
        const order = this.pos.get_order();
        const pay_line = order.get_selected_paymentline();
        
        if (!pay_line) {
            this._showError(_t("No payment line selected"), "Paylands Error");
            return false;
        }

        if (pay_line.amount > 0) {
            return await this._doSend(false);
        } else {
            const { confirmed, payload: code } = await this.env.services.dialog.add(TextInputPopup, {
                title: _t('Número de pedido (Order) original'),
                body: _t('Ej.: 00001-051-0001.'),
            });
            if (confirmed && code) {
                console.log("return: " + code);
                return await this._doSend(code);
            }
        }
        return false;
    }

    _showError(msg, title) {
        if (!title) {
            title = _t("Paylands Error");
        }
        this.env.services.dialog.add(AlertDialog, {
            title: title,
            body: msg,
        });
    }
}