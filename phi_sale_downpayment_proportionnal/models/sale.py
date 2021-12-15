# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_invoiceable_lines(self, final=False):
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if not line.is_downpayment:
                    if pending_section:
                        invoiceable_line_ids.append(pending_section.id)
                        pending_section = None
                    invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids)

    def _create_invoices(self, grouped=False, final=False, date=None):
        invoices = super(SaleOrder, self)._create_invoices(grouped, final, date)
        if final:
            for invoice in invoices:
                orders = invoice.mapped('invoice_line_ids.sale_line_ids.order_id')
                order_amount_untaxed = sum(order.amount_untaxed for order in orders)
                if order_amount_untaxed:
                    proportion = invoice.amount_untaxed / order_amount_untaxed
                    for order in orders:
                        down_payment_lines = order.order_line.filtered(lambda sale_order_line: sale_order_line.is_downpayment)
                        for down_payment_line in down_payment_lines:
                            acccount_line = self.env['account.move.line']
                            price = down_payment_line.price_unit
                            res = {
                                'sequence': 999,
                                'name': down_payment_line.name,
                                'product_id': down_payment_line.product_id.id,
                                'product_uom_id': down_payment_line.product_id.uom_id.id,
                                'quantity': proportion * -1,
                                'price_unit': price,
                                'move_id': invoice.id,
                            }
                            new_line = acccount_line.new(res)
                            new_line.account_id = new_line._get_computed_account()
                            new_line._onchange_product_id()
                            new_line.price_unit = price
                            invoice.with_context(check_move_validity=False).line_ids += new_line
                        invoice.with_context(check_move_validity=False)._recompute_dynamic_lines(
                            recompute_all_taxes=True, recompute_tax_base_amount=True)
        return invoices

