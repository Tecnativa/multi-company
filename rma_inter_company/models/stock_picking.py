# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        # Auto-done RMA IN Company A
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_rma_origin_reception()
        ):
            done_moves = picking.move_ids.filtered(lambda x: x.state == "done")
            rmas = done_moves.rma_receiver_ids.intercompany_origin_rma_id.sudo()
            pending_rma_reception_pickings = rmas.reception_move_id.picking_id.filtered(
                lambda x: x.state == "assigned"
            )
            if pending_rma_reception_pickings:
                pending_rma_reception_pickings.button_validate()
        # Auto-done RMA IN Company B
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_rma_reception()
        ):
            done_moves = picking.move_ids.filtered(lambda x: x.state == "done")
            rmas = done_moves.rma_receiver_ids.intercompany_rma_id.sudo()
            pending_rma_reception_pickings = rmas.reception_move_id.picking_id.filtered(
                lambda x: x.state == "assigned"
            )
            if pending_rma_reception_pickings:
                pending_rma_reception_pickings.button_validate()
        # Auto-done RMA OUT Company A
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_origin_rma_delivery()
        ):
            rmas = picking.move_ids.rma_id.intercompany_origin_rma_id.sudo()
            rma_delivery_pickings = rmas.delivery_move_ids.picking_id
            confirmed_rma_delivery_pickings = rma_delivery_pickings.filtered(
                lambda x: x.state == "confirmed"
            )
            if confirmed_rma_delivery_pickings:
                # Tip for replace
                confirmed_rma_delivery_pickings.action_assign()
            pending_rma_delivery_pickings = rma_delivery_pickings.filtered(
                lambda x: x.state == "assigned"
            )
            if pending_rma_delivery_pickings:
                pending_rma_delivery_pickings.button_validate()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        # Auto-cancel RMA OUT Company A
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_origin_rma_delivery()
        ):
            rmas = picking.move_ids.rma_id.intercompany_origin_rma_id.sudo()
            pending_rma_delivery_pickings = rmas.delivery_move_ids.picking_id.filtered(
                lambda x: x.state not in ("done", "cancel")
            )
            if pending_rma_delivery_pickings:
                pending_rma_delivery_pickings.action_cancel()
        return res

    def _is_intercompany_rma_reception(self):
        return any(m.move_ids.rma_receiver_ids.intercompany_rma_id for m in self.sudo())

    def _is_intercompany_rma_origin_reception(self):
        return any(
            m.move_ids.rma_receiver_ids.intercompany_origin_rma_id for m in self.sudo()
        )

    def _is_intercompany_origin_rma_delivery(self):
        return any(m.move_ids.rma_id.intercompany_origin_rma_id for m in self.sudo())
