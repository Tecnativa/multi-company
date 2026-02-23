# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Rma(models.Model):
    _inherit = "rma"

    intercompany_rma_id = fields.Many2one(
        comodel_name="rma",
        string="Intercompany RMA",
        readonly=True,
        copy=False,
    )
    intercompany_origin_rma_id = fields.Many2one(
        comodel_name="rma",
        string="Intercompany Origin RMA",
        readonly=True,
        copy=False,
    )

    def _get_location_final(self):
        if self.intercompany_origin_rma_id:
            return self.env.ref("stock.stock_location_inter_company")
        return super()._get_location_final()

    def _get_intercompany_sale_line(self):
        self.ensure_one()
        return self.move_id.purchase_line_id.intercompany_sale_line_id

    def _create_intercompany_rma(self):
        for item in self.filtered(lambda x: not x.intercompany_rma_id):
            sol = item._get_intercompany_sale_line()
            if not sol:
                continue
            # Create the RMA based on the corresponding sales order
            res = sol.sudo().order_id.action_create_rma()
            # We need to use sudo() because the user likely doesn't have access
            # to the other company or hasn't selected it
            wizard = self.env[res["res_model"]].browse(res["res_id"]).sudo()
            wizard_line = wizard.line_ids.filtered(
                lambda x, sol=sol: x.sale_line_id == sol
            )
            wizard_line.operation_id = item.operation_id
            wizard_line.quantity = wizard_line.allowed_quantity
            new_rma = wizard.create_rma()
            new_rma.intercompany_origin_rma_id = item
            item.intercompany_rma_id = new_rma
            if new_rma.state == "draft":
                new_rma.action_confirm()

    def _get_intercompany_rmas(self):
        intercompany_rmas = self.mapped("intercompany_rma_id").sudo()
        intercompany_rmas += self.mapped("intercompany_origin_rma_id").sudo()
        return intercompany_rmas

    def action_confirm(self):
        self._create_intercompany_rma()
        res = super().action_confirm()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_confirm = intercompany_rmas.filtered(
            lambda x: x.state != "confirmed"
        )
        if intercompany_rmas_to_confirm:
            intercompany_rmas_to_confirm.action_confirm()
        return res

    def action_cancel(self):
        """Perform the same action in the intercompany RMAs."""
        res = super().action_cancel()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_cancel = intercompany_rmas.filtered(
            lambda x: x.state != "cancelled"
        )
        if intercompany_rmas_to_cancel:
            intercompany_rmas_to_cancel.action_cancel()
        return res

    def action_draft(self):
        """Perform the same action in the intercompany RMAs."""
        res = super().action_draft()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_draft = intercompany_rmas.filtered(
            lambda x: x.state != "draft"
        )
        if intercompany_rmas_to_draft:
            intercompany_rmas_to_draft.action_draft()
        return res

    def create_replace(self, scheduled_date, warehouse, product, qty, uom):
        """Perform the same action in the intercompany RMA."""
        if not self.env.context.get("skip_intercompany_rma_replace"):
            intercompany_rma = self.intercompany_rma_id.sudo()
            if intercompany_rma and intercompany_rma.can_be_replaced:
                # It is important to use the right warehouse, the one belonging
                # to the right company
                intercompany_rma.with_context(
                    skip_intercompany_rma_replace=True
                ).create_replace(
                    scheduled_date=scheduled_date,
                    warehouse=intercompany_rma.warehouse_id,
                    product=product,
                    qty=qty,
                    uom=uom,
                )
        self = self.filtered(lambda x: x.can_be_replaced)
        if not self:
            return
        res = super().create_replace(
            scheduled_date=scheduled_date,
            warehouse=warehouse,
            product=product,
            qty=qty,
            uom=uom,
        )
        origin_rma = self.intercompany_origin_rma_id.sudo()
        if origin_rma and origin_rma.can_be_replaced:
            # It is important to use the right warehouse, the one belonging
            # to the right company
            origin_rma.with_context(skip_intercompany_rma_replace=True).create_replace(
                scheduled_date, origin_rma.warehouse_id, product, qty, uom
            )
        return res

    def create_return(self, scheduled_date, qty=None, uom=None):
        """Perform the same action in the intercompany RMAs."""
        res = super().create_return(scheduled_date=scheduled_date, qty=qty, uom=uom)
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_return = intercompany_rmas.filtered(
            lambda x: x.can_be_returned
        )
        if intercompany_rmas_to_return:
            intercompany_rmas_to_return.create_return(scheduled_date, qty, uom)
        return res

    def action_refund(self):
        """Perform the same action in the intercompany RMAs."""
        res = super().action_refund()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_refund = intercompany_rmas.filtered(
            lambda x: x.can_be_refunded
        )
        if intercompany_rmas_to_refund:
            intercompany_rmas_to_refund.action_refund()
        return res
