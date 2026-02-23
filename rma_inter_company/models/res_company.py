# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    intercompany_rma = fields.Boolean(string="Inter Company RMA")
    intercompany_rma_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Inter Company RMA Company",
    )
    intercompany_rma_domain = fields.Char(
        string="Inter Company RMA Domain", default="[]"
    )
    intercompany_rma_team_id = fields.Many2one(
        comodel_name="rma.team",
        string="Inter Company RMA Team",
        domain="['|', ('company_id', '=', intercompany_rma_company_id), ('company_id', '=', False)]",  # noqa: E501
    )
    intercompany_rma_user_id = fields.Many2one(
        comodel_name="res.users", string="Inter Company RMA User"
    )
