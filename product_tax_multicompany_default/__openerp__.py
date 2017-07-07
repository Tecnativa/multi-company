# -*- coding: utf-8 -*-
# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Product Tax Multi Company Default',
    'summary': """
        This modules set default taxes when product create and adds
        a button to set not default taxes matching by code.""",
    'version': '9.0.1.0.0',
    'category': 'Account',
    'website': 'http://www.tecnativa.com',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'product',
    ],
    'data': [
        'views/product_template_view.xml',
    ],
}
