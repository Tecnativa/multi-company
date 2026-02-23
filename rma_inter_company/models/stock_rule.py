# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        move_values = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        inter_loc = self.env.ref(
            "stock.stock_location_inter_company", raise_if_not_found=False
        )
        if values.get("rma_receiver_ids"):
            rma_ids = values.get("rma_receiver_ids")[0][2]
            rma = self.env["rma"].browse(rma_ids)
            if rma.intercompany_rma_id:
                # It is important to define the correct destination location. You cannot
                # define this location in the corresponding RMA because that would imply
                # that no rule was found in the RMA IN route. Creating a rule with the
                # Intercompany destination location would not be a solution, as it would
                # have many unintended consequences.
                move_values["location_dest_id"] = inter_loc.id
            elif rma.intercompany_origin_rma_id:
                move_values["location_id"] = inter_loc.id
        elif values.get("rma_id"):
            rma = self.env["rma"].browse(values.get("rma_id"))
            if rma.intercompany_rma_id:
                move_values["location_id"] = inter_loc.id
        return move_values
