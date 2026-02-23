# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from ast import literal_eval

from odoo import Command, fields, models


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

    def _get_intercompany_rma_company(self):
        """This method returns the company in which the intercompany RMA will be
        created. It is possible to use it and modify the value by referring to
        another field (for example, sale_line_id.auto_purchase_line_id.intercompany_sale_line_id.company_id
        if purchase_sale_stock_inter_company is used).
        """  # noqa: E501
        self.ensure_one()
        return self.company_id.intercompany_rma_company_id

    def _prepare_intercompany_rma_values(self):
        self.ensure_one()
        company = self._get_intercompany_rma_company()
        team = self.company_id.intercompany_rma_team_id
        user = self.company_id.intercompany_rma_user_id
        warehouse = (
            self.env["stock.warehouse"]
            .sudo()
            .search([("company_id", "=", company.id)], limit=1)
        )
        partner = company.sudo().partner_id
        vals = {
            "company_id": company.id,
            "partner_id": partner.id,
            "partner_shipping_id": partner.id,
            "partner_invoice_id": partner.id,
            "intercompany_origin_rma_id": self.id,
            "team_id": team.id if team else False,
            "user_id": user.id if user else False,
            # Do not copy the picking because it belongs to another company.
            "picking_id": False,
            # Do not copy the move because it belongs to another company.
            "move_id": False,
            # Appropriate location_id because the warehouse is not the same
            "location_id": warehouse.rma_loc_id.id,
        }
        if "order_id" in self._fields:
            vals["order_id"] = False
        return vals

    def _valid_create_intercompany_rma(self):
        """Conditions that determine whether an intercompany RMA should be
        created.
        """
        self.ensure_one()
        company = self.company_id
        domain = company.intercompany_rma_domain
        return bool(
            self.filtered_domain(literal_eval(domain))
            if company.intercompany_rma and not self.sudo().intercompany_rma_id
            else False
        )

    def _create_intercompany_rma(self):
        for item in self.filtered(lambda x: x.state == "draft"):
            if item._valid_create_intercompany_rma():
                rma = item.sudo().copy(item._prepare_intercompany_rma_values())
                item.intercompany_rma_id = rma
                rma.action_confirm()

    def action_confirm(self):
        if not self.env.context.get("skip_intercompany_rma_confirm"):
            for item in self.filtered(lambda x: x.intercompany_origin_rma_id):
                intercompany_origin_rma = item.intercompany_origin_rma_id.sudo()
                intercompany_origin_rma.with_context(
                    skip_intercompany_rma_confirm=True,
                ).action_confirm()
            for item in self.filtered(lambda x: x.intercompany_rma_id):
                rmas_to_confirm = item + item.intercompany_rma_id
                rmas_to_confirm.with_context(
                    skip_intercompany_rma_confirm=True,
                ).sudo().action_confirm()
        self._create_intercompany_rma()
        return super().action_confirm()

    def _prepare_reception_procurement_vals(self, group=None):
        """Need to delete values that belong to another company."""
        vals = super()._prepare_reception_procurement_vals(group=group)
        if self.intercompany_origin_rma_id:
            vals.pop("origin_returned_move_id", None)
            vals.pop("sale_line_id", None)
            vals["move_orig_ids"] = [
                Command.set(self.intercompany_origin_rma_id.reception_move_id.ids)
            ]
        return vals

    def _prepare_delivery_procurement_vals(self, scheduled_date=None):
        vals = super()._prepare_delivery_procurement_vals(scheduled_date=scheduled_date)
        if self.intercompany_rma_id:
            vals["move_orig_ids"] = [
                Command.set(self.intercompany_rma_id.sudo().delivery_move_ids.ids)
            ]
        return vals

    def _prepare_replace_procurement_vals(self, warehouse=None, scheduled_date=None):
        vals = super()._prepare_replace_procurement_vals(
            warehouse=warehouse, scheduled_date=scheduled_date
        )
        if self.intercompany_rma_id:
            vals["move_orig_ids"] = [
                Command.set(self.intercompany_rma_id.sudo().delivery_move_ids.ids)
            ]
        return vals

    def action_cancel(self):
        """Perform the same action in the intercompany RMA."""
        res = super().action_cancel()
        if not self.env.context.get("skip_intercompany_rma_cancel"):
            intercompany_rmas = self.mapped("intercompany_rma_id").sudo()
            intercompany_rmas.with_context(
                skip_intercompany_rma_cancel=True
            ).action_cancel()
        if not self.env.context.get("skip_intercompany_origin_rma_cancel"):
            intercompany_origin_rmas = self.mapped("intercompany_origin_rma_id").sudo()
            intercompany_origin_rmas.with_context(
                skip_intercompany_origin_rma_cancel=True
            ).action_cancel()
        return res

    def action_draft(self):
        """Perform the same action in the intercompany RMA."""
        res = super().action_draft()
        if not self.env.context.get("skip_intercompany_rma_draft"):
            intercompany_rmas = self.mapped("intercompany_rma_id").sudo()
            intercompany_rmas.with_context(
                skip_intercompany_rma_draft=True
            ).action_draft()
        if not self.env.context.get("skip_intercompany_origin_rma_draft"):
            intercompany_origin_rmas = self.mapped("intercompany_origin_rma_id").sudo()
            intercompany_origin_rmas.with_context(
                skip_intercompany_origin_rma_draft=True
            ).action_draft()
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
        """Perform the same action in the intercompany RMA."""
        for item in self.filtered(lambda x: x.intercompany_rma_id):
            intercompany_rma = item.intercompany_rma_id.sudo()
            intercompany_rma.create_return(scheduled_date, qty, uom)
        self = self.filtered(lambda x: x.can_be_returned)
        if not self:
            return
        res = super().create_return(scheduled_date=scheduled_date, qty=qty, uom=uom)
        for item in self.filtered(lambda x: x.intercompany_origin_rma_id):
            intercompany_origin_rma = item.intercompany_origin_rma_id.sudo()
            intercompany_origin_rma.create_return(scheduled_date, qty, uom)
        return res
