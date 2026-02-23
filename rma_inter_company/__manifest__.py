# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Inter Company Module for RMA",
    "version": "18.0.1.0.0",
    "category": "Purchase Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["rma"],
    "data": [
        "views/res_config_settings_view.xml",
        "views/rma_views.xml",
    ],
    "maintainers": ["victoralmau"],
}
