# -*- coding: utf-8 -*-
{
    'name': "Phidias : specifique Nexans",

    'summary': """
        Phidias : specifique Nexans
        """,

    'description': """
        Phidias : specifique Nexans
    """,

    'author': "Phidias",
    'website': "http://www.phidias.fr",
    'category': 'Uncategorized',
    'version': '14.0.0.22',

    # any module necessary for this one to work correctly
    'depends': [
        'crm',
        'sale_management',
        'account',
        'stock',
        'project',
        'purchase',
        'account_accountant',
        'helpdesk',
        'approvals',
        'l10n_fr',
        'l10n_fr_reports',
        'l10n_fr_fec',
        'web_studio',
        'phi_analytic_account_order_from_sale_to_purchase',
        'phi_purchase_analytic_account_order_header',
        'sale_margin',
        'sales_delivery_date',
        'phi_cash_flow',
        'phi_product_prototype',
        'phi_crm_competitors',
        'phi_requisition_from_sale_order',
        'phi_sale_customer_incoterm',
        'phi_sale_line_change_margin_pct',
        'phi_sale_payment_method',
        'product_approval_management',
        'phi_crm_others_contacts',
        'phi_customer_insured_amount',
        'phi_helpdesk_purchase',
        'phi_order_mail_with_product_attachments',
        'phi_product_last_purchase_info',
        'phi_product_substitute',
        'phi_purchase_category',
        'phi_purchase_price_index',
        'phi_purchase_receipt_by_date',
        'phi_purchase_vendor_incoterm',
        'phi_quadra_export',
        'phi_vendor_buyer',
        'phi_webstudio_approval_activity',
        'product_code_unique',
        'product_sequence',
        'sales_delivery_date',
        'phi_incoterm_description',
        'sale_quotation_number',
        'phi_purchase_quotation_number',
        'phi_purchase_supplierinfo_perqty',
        #'account_move_csv_import',
        'purchase_vendorbill_advance',
        'purchase_vendorbill_advance_proportionnal',
    ],
    "data": [
        'views/crm_lead_views.xml',
        'views/purchase_order.xml',
        'data/approbation_rule.xml',
        'views/sale_order_views.xml',
        'report/sale_order_report_templates.xml',
        'report/report_deliveryslip.xml',
        'views/stock_picking_views.xml',
    ]
}
