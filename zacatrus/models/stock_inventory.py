# © 2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    def action_generate_putaway_rules(self):
        _logger.warning("action_generate_putaway_rules")
        self._generate_putaway_rules()

    def _generate_putaway_rules(self):
        _logger.warning("stock.inventory _generate_putaway_rules")
        for record in self:
            if record.state != "done":
                raise ValidationError(
                    _(
                        "Please validate the inventory before generating "
                        "the putaway strategy."
                    )
                )
            _logger.warning(f"Para las siguientes lines {record.line_ids.ids} llamo a _generate_putaway_rules con location {record.location_ids.ids}")
            record.line_ids._generate_putaway_rules(record.location_ids)


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _generate_putaway_rules(self, inventory_locations):
        _logger.warning("stock.inventory.line _generate_putaway_rules")
        
        # Eliminate lines for other IN locations
        # and eliminate lines where quantity is null
        for location_in in inventory_locations:
            _logger.warning("location_in %s" % location_in)
            _logger.warning("Para las siguiente lineas %s" % self.filtered(
                lambda x: x.product_qty > 0
                and x.location_id.id in location_in.children_ids.ids
            ).ids)
            
            self.filtered(
                lambda x: x.product_qty > 0
                and x.location_id.id in location_in.children_ids.ids
            )._update_product_putaway_rule(location_in)

    def _update_product_putaway_rule(self, location_in):
        _logger.warning("stock.inventory.line _update_product_putaway_rule")
        putaway_rule_obj = self.env["stock.putaway.rule"]
        putaway_rules = putaway_rule_obj.search(
            [
                ("product_id", "in", self.mapped("product_id").ids),
                ("location_in_id", "=", location_in.id),
            ]
        )
        for record in self:
            putaway_rule = putaway_rules.filtered(
                lambda x: x.product_id == record.product_id
            )
            _logger.warning("putaway_rule %s" % putaway_rule)
            if putaway_rule:
                _logger.warning("Actualizo location out por %s" % record.location_id.id)
                putaway_rule.location_out_id = record.location_id
            else:
                _logger.warning("Creo putaway_rule")
                putaway_rule_obj.create(
                    {
                        "product_id": record.product_id.id,
                        "location_in_id": location_in.id,
                        "location_out_id": record.location_id.id,
                    }
                )