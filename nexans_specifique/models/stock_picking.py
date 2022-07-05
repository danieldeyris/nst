# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_nb = fields.Integer("Package #", compute="_compute_package_nb")
    sale_order_origin = fields.Char("Sale Order Origin", compute="_compute_sale_order_origin")
    commercial_invoice = fields.Char("Commercial invoice")
    partner_order_id = fields.Many2one('res.partner', string='Partner', compute='_compute_from_order')
    total_gross_weight = fields.Float("Total Gross Weight")
    total_gross_weight_print = fields.Float("Total Gross Weight", compute="_compute_total_gross_weight_print")
    incoterm = fields.Many2one('account.incoterms', 'Incoterm', compute='_compute_from_order')
    incoterm_description = fields.Text("Incoterm Description", compute='_compute_from_order')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Project', compute='_compute_from_order')
    amount_subtotal = fields.Monetary(
        compute="_compute_amount_subtotal",
        string="Total",
        compute_sudo=True,
    )
    currency_id = fields.Many2one('res.currency', string="Sale Currency", compute='_compute_from_order')

    def _compute_package_nb(self):
        for picking in self:
            picking.package_nb = len(picking.package_ids)

    def _compute_sale_order_origin(self):
        for picking in self:
            sale_orders = picking.purchase_id._get_sale_orders().mapped('name')
            picking.sale_order_origin = ", ".join(sale_orders)

    def _compute_from_order(self):
        for picking in self:
            sale = False
            if not picking.sale_id:
                sale_orders = picking.purchase_id._get_sale_orders()
                if len(sale_orders):
                    sale = sale_orders[0]
            else:
                sale = picking.sale_id
            picking.partner_order_id = sale.partner_id if sale else False
            picking.incoterm = sale.incoterm if sale else False
            picking.incoterm_description = sale.incoterm_description if sale else False
            picking.analytic_account_id = sale.analytic_account_id if sale else False
            picking.currency_id = sale.currency_id if sale else False

    def _compute_total_gross_weight_print(self):
        for picking in self:
            picking.total_gross_weight_print = picking.total_gross_weight or picking.shipping_weight

    def _compute_amount_subtotal(self):
        for picking in self:
            picking.amount_subtotal = sum(picking.move_line_ids.mapped('sale_price_subtotal'))

    def _action_done(self):
        results = []
        for rec in self:
            result = super(StockPicking, self)._action_done()
            if rec.location_dest_id.usage == 'customer':
                rec.commercial_invoice = self.env['ir.sequence'].next_by_code('nexans_specifique.commercial.invoice')
            results.append(result)
        return results
