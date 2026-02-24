# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    company_ids = fields.Many2many(
        string="Companies",
        related="partner_id.company_ids",
    )
