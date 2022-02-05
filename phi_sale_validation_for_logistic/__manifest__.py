# -*- coding: utf-8 -*-
{
    'name': "Phidias Validation for logistic",

    'summary': """
        Phidias Validation for logistic
        """,

    'description': """
        Phidias Validation for logistic
    """,

    'author': "Phidias",
    'website': "http://www.phidias.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
    ],

    # always loaded
    'data': [
        'security/sale_security.xml',
        'views/sale.xml',
    ],
}
