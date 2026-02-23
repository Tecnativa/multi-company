# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, new_test_user
from odoo.tools import mute_logger

from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaInterCompany(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.intercompany_location = cls.env.ref("stock.stock_location_inter_company")
        cls.company_a = cls.company
        cls.warehouse_a = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_a.id)]
        )
        customer_loc, _supplier_loc = cls.warehouse_a._get_partner_locations()
        cls.customer_loc = customer_loc
        cls.warehouse_a.rma_out_replace_route_id = cls.warehouse_a.rma_out_route_id
        cls.company_b = cls.env["res.company"].create({"name": "Test company B"})
        cls.warehouse_b = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_b.id)]
        )
        cls.warehouse_b.rma_out_replace_route_id = cls.warehouse_b.rma_out_route_id
        cls.team_b = cls.env["rma.team"].create(
            {
                "name": "Test team B",
                "company_id": cls.company_b.id,
            }
        )
        cls.company_a.write(
            {
                "name": "Test company A",
                "intercompany_rma": True,
                "intercompany_rma_company_id": cls.company_b.id,
                "intercompany_rma_domain": "[]",
                "intercompany_rma_team_id": cls.team_b.id,
            }
        )
        cls.rma_user_a = new_test_user(
            cls.env,
            login="test-rma_user-a",
            groups="rma.rma_group_user_all,stock.group_stock_user",
            company_id=cls.company_a.id,
            company_ids=[Command.set((cls.company_a).ids)],
        )
        cls.rma_user_b = new_test_user(
            cls.env,
            login="test-rma_user-b",
            groups="rma.rma_group_user_all,stock.group_stock_user",
            company_id=cls.company_b.id,
            company_ids=[Command.set((cls.company_b).ids)],
        )
        cls.team_b.write(
            {
                "member_ids": [Command.set(cls.rma_user_b.ids)],
            }
        )
        cls.company_a.intercompany_rma_user_id = cls.rma_user_b
        cls._update_available_quantity(cls.product, cls.warehouse_a.lot_stock_id, 1)
        cls.picking_a = cls._create_picking(cls.warehouse_a)
        cls._update_available_quantity(cls.product, cls.warehouse_b.lot_stock_id, 1)
        cls.picking_b = cls._create_picking(cls.warehouse_b)

    @classmethod
    def _update_available_quantity(self, product, location, qty):
        self.env["stock.quant"]._update_available_quantity(product, location, qty)

    @classmethod
    def _create_picking(self, warehouse):
        picking_form = Form(
            record=self.env["stock.picking"].with_context(
                default_picking_type_id=warehouse.out_type_id.id
            ),
            view="stock.view_picking_form",
        )
        picking_form.partner_id = self.partner
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.button_validate()
        return picking

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_b(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_b.with_user(self.rma_user_b).action_cancel()
        self.assertEqual(rma_a.state, "cancelled")
        self.assertEqual(rma_b.state, "cancelled")
        rma_b.with_user(self.rma_user_b).action_draft()
        self.assertEqual(rma_a.state, "draft")
        self.assertEqual(rma_b.state, "draft")
        rma_b.with_user(self.rma_user_b).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_b.state, "confirmed")

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_a(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a.with_user(self.rma_user_a).action_cancel()
        self.assertEqual(rma_a.state, "cancelled")
        self.assertEqual(rma_b.state, "cancelled")
        rma_a.with_user(self.rma_user_a).action_draft()
        self.assertEqual(rma_a.state, "draft")
        self.assertEqual(rma_b.state, "draft")
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_b.state, "confirmed")

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_a(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Return rma A
        res = rma_a.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_b.state, "waiting_return")
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(rma_a.state, "waiting_return")
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        rma_a_delivery_picking.with_user(self.rma_user_a).action_cancel()
        self.assertEqual(rma_a_delivery_picking.state, "cancel")
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(rma_b.state, "waiting_return")
        rma_b_delivery_picking.with_user(self.rma_user_b).action_cancel()
        self.assertEqual(rma_b_delivery_picking.state, "cancel")
        self.assertEqual(rma_b.state, "received")

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_b(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Return rma A
        res = rma_a.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_b.state, "waiting_return")
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(rma_a.state, "waiting_return")
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        rma_b_delivery_picking.with_user(self.rma_user_b).action_cancel()
        self.assertEqual(rma_a_delivery_picking.state, "confirmed")
        self.assertEqual(rma_b_delivery_picking.state, "cancel")
        self.assertEqual(rma_a.state, "waiting_return")
        self.assertEqual(rma_b.state, "received")
        rma_a_delivery_picking.with_user(self.rma_user_a).action_cancel()
        self.assertEqual(rma_a_delivery_picking.state, "cancel")
        self.assertEqual(rma_a.state, "received")

    def test_rma_intercompany_condition_ok(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        self.company.intercompany_rma_domain = (
            f"[('product_id', '=', {self.product.id})]"
        )
        rma_a.action_confirm()
        self.assertTrue(rma_a.intercompany_rma_id)

    def test_rma_intercompany_condition_ko(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        self.company.intercompany_rma_domain = "[('product_id', '=', False)]"
        rma_a.action_confirm()
        self.assertFalse(rma_a.intercompany_rma_id)

    def test_rma_intercompany_full_company_b(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a.picking_id = self.picking_a
        self.assertTrue(rma_a.move_id)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_a.warehouse_id, self.warehouse_a)
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.company_id, self.company_b)
        self.assertEqual(rma_b.partner_id, self.company_b.partner_id)
        self.assertEqual(rma_b.warehouse_id, self.warehouse_b)
        self.assertEqual(rma_b.location_id, self.warehouse_b.rma_loc_id)
        self.assertEqual(rma_b.team_id, self.team_b)
        self.assertEqual(rma_b.user_id, self.rma_user_b)
        self.assertEqual(rma_b.intercompany_origin_rma_id, rma_a)
        self.assertEqual(rma_b.state, "confirmed")
        self.assertFalse(rma_b.picking_id)
        self.assertFalse(rma_b.move_id)
        self.assertEqual(rma_b.reception_move_id.move_orig_ids, rma_a.reception_move_id)
        self.assertFalse(rma_b.reception_move_id.origin_returned_move_id)
        self.assertEqual(
            rma_b.reception_move_id.location_id, self.intercompany_location
        )
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_a.intercompany_rma_id, rma_b)
        self.assertEqual(
            rma_a.reception_move_id.location_dest_id, self.intercompany_location
        )
        self.assertTrue(rma_a.reception_move_id.origin_returned_move_id)
        self.assertEqual(rma_b_reception_picking.state, "waiting")
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(rma_b_reception_picking.state, "assigned")
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b.state, "received")
        # Return rma B
        res = rma_b.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_b).action_deliver()
        self.assertEqual(rma_b.state, "waiting_return")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(rma_a.state, "waiting_return")
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        rma_b_delivery_picking.move_ids.quantity = 1
        rma_b_delivery_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "returned")
        self.assertEqual(rma_a_delivery_picking.state, "assigned")
        rma_a_delivery_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "returned")

    def test_rma_intercompany_full_company_a(self):
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a.picking_id = self.picking_a
        self.assertTrue(rma_a.move_id)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_a.warehouse_id, self.warehouse_a)
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.company_id, self.company_b)
        self.assertEqual(rma_b.partner_id, self.company_b.partner_id)
        self.assertEqual(rma_b.warehouse_id, self.warehouse_b)
        self.assertEqual(rma_b.location_id, self.warehouse_b.rma_loc_id)
        self.assertEqual(rma_b.team_id, self.team_b)
        self.assertEqual(rma_b.user_id, self.rma_user_b)
        self.assertEqual(rma_b.intercompany_origin_rma_id, rma_a)
        self.assertEqual(rma_b.state, "confirmed")
        self.assertFalse(rma_b.picking_id)
        self.assertFalse(rma_b.move_id)
        self.assertEqual(rma_b.reception_move_id.move_orig_ids, rma_a.reception_move_id)
        self.assertFalse(rma_b.reception_move_id.origin_returned_move_id)
        self.assertEqual(
            rma_b.reception_move_id.location_id, self.intercompany_location
        )
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_a.intercompany_rma_id, rma_b)
        self.assertEqual(
            rma_a.reception_move_id.location_dest_id, self.intercompany_location
        )
        self.assertTrue(rma_a.reception_move_id.origin_returned_move_id)
        self.assertEqual(rma_b_reception_picking.state, "waiting")
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(rma_b_reception_picking.state, "assigned")
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b.state, "received")
        # Return rma A
        res = rma_a.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_a.state, "waiting_return")
        self.assertEqual(rma_b.state, "waiting_return")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        rma_b_delivery_picking.move_ids.quantity = 1
        rma_b_delivery_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "returned")
        self.assertEqual(rma_a_delivery_picking.state, "assigned")
        rma_a_delivery_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "returned")

    def test_rma_intercompany_replace_full_company_b(self):
        self._update_available_quantity(
            self.product_2, self.warehouse_b.lot_stock_id, 1
        )
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.move_ids.quantity = 1
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "assigned")
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Replace rma B
        res = rma_b.action_replace()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.product_id = self.product_2
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_b).action_deliver()
        self.assertEqual(rma_b.state, "waiting_replacement")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        self.assertEqual(rma_b.delivery_move_ids.product_id, self.product_2)
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(rma_a.state, "waiting_replacement")
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        self.assertEqual(rma_a.delivery_move_ids.product_id, self.product_2)
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_a_delivery_picking.state, "waiting")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        self.assertEqual(rma_b_delivery_picking.state, "confirmed")
        rma_b_delivery_picking.move_ids.quantity = 1
        rma_b_delivery_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "replaced")
        self.assertEqual(rma_a_delivery_picking.state, "assigned")
        rma_a_delivery_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "replaced")

    def test_rma_intercompany_replace_full_company_a(self):
        self.operation.action_create_delivery = "manual_on_confirm"
        self._update_available_quantity(
            self.product_2, self.warehouse_b.lot_stock_id, 1
        )
        rma_a = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.move_ids.quantity = 1
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "assigned")
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Replace rma A
        res = rma_a.action_replace()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.product_id = self.product_2
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_b.state, "waiting_replacement")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        self.assertEqual(rma_b.delivery_move_ids.product_id, self.product_2)
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(rma_a.state, "waiting_replacement")
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        self.assertEqual(rma_a.delivery_move_ids.product_id, self.product_2)
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_a_delivery_picking.state, "waiting")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        self.assertEqual(rma_b_delivery_picking.state, "confirmed")
        rma_b_delivery_picking.move_ids.quantity = 1
        rma_b_delivery_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "replaced")
        self.assertEqual(rma_a_delivery_picking.state, "assigned")
        rma_a_delivery_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "replaced")

    def test_rma_not_intercompany(self):
        rma_b = self._create_rma(
            self.partner, self.product, 1, self.warehouse_b.rma_loc_id
        )
        rma_b.company_id = self.company_b
        rma_b.picking_id = self.picking_b
        self.assertTrue(rma_b.move_id)
        rma_b = rma_b.with_user(self.rma_user_b)
        rma_b.with_user(self.rma_user_b).action_confirm()
        self.assertEqual(rma_b.state, "confirmed")
        self.assertEqual(rma_b.warehouse_id, self.warehouse_b)
        self.assertEqual(rma_b.location_id, self.warehouse_b.rma_loc_id)
        self.assertEqual(rma_b.state, "confirmed")
        self.assertEqual(rma_b.reception_move_id.location_id, self.customer_loc)
        self.assertEqual(
            rma_b.reception_move_id.location_dest_id, self.warehouse_b.rma_loc_id
        )
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
