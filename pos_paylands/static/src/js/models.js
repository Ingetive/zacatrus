/** @odoo-module **/

import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaylandsPayment } from "@pos_paylands/js/payment_terminal";

register_payment_method("paylands_payment", PaylandsPayment);