# -*- coding: utf-8 -*-
{
    'name': "Phidias : Purchase price index",

    'summary': """
        Phidias : Purchase price index
        """,

    'description': """
        Phidias : Purchase price index
    """,

    'author': "Phidias",
    'website': "http://www.phidias.fr",
    'category': 'Uncategorized',
    'version': '14.0.0.4',

    # any module necessary for this one to work correctly
    'depends': [
        'purchase',
    ],
    "data": [
        'views/purchase_index.xml',
        'security/ir.model.access.csv',
        'views/product.xml',
    ]
}
