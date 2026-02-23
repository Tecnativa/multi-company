# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _skip_push(self):
        """We use sudo() if there is an RMA receipt transaction involving another
        company to prevent a UX access error if Company A's receipt form has been
        validated.
        """
        if any(
            m.sudo().rma_receiver_ids and m.sudo().rma_receiver_ids.intercompany_rma_id
            for m in self
        ) or any(
            m.sudo().rma_id and m.sudo().rma_id.intercompany_origin_rma_id for m in self
        ):
            self = self.sudo()
        return super()._skip_push()

    def _action_cancel(self):
        if any(
            m.sudo().rma_receiver_ids
            and (
                m.sudo().rma_receiver_ids.intercompany_rma_id
                or m.sudo().rma_receiver_ids.intercompany_origin_rma_id
            )
            for m in self
        ) or any(
            m.sudo().rma_id
            and (
                m.sudo().rma_id.intercompany_rma_id
                or m.sudo().rma_id.intercompany_origin_rma_id
            )
            for m in self
        ):
            self = self.sudo()
        return super()._action_cancel()
