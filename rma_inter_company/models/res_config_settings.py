# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    intercompany_rma = fields.Boolean(
        related="company_id.intercompany_rma",
        readonly=False,
    )
    intercompany_rma_company_id = fields.Many2one(
        related="company_id.intercompany_rma_company_id",
        readonly=False,
    )
    intercompany_rma_domain = fields.Char(
        related="company_id.intercompany_rma_domain",
        readonly=False,
    )
    intercompany_rma_team_id = fields.Many2one(
        related="company_id.intercompany_rma_team_id",
        readonly=False,
    )
    intercompany_rma_user_id = fields.Many2one(
        related="company_id.intercompany_rma_user_id",
        readonly=False,
    )
