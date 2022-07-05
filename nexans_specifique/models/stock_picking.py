# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_nb = fields.Integer("Package #", compute="_compute_package_nb")
    sale_order_origin = fields.Char("Sale Order Origin", compute="_compute_sale_order_origin")
    commercial_invoice = fields.Char("Commercial invoice")
    partner_order_id = fields.Many2one('res.partner', string='Partner', compute='_compute_partner_order')
    total_gross_weight = fields.Float("Total Gross Weight")
    total_gross_weight_print = fields.Float("Total Gross Weight", compute="_compute_total_gross_weight_print")

    def _compute_package_nb(self):
        for picking in self:
            picking.package_nb = len(picking.package_ids)

    def _compute_sale_order_origin(self):
        for picking in self:
            sale_orders = picking.purchase_id._get_sale_orders().mapped('name')
            picking.sale_order_origin = ", ".join(sale_orders)

    def _compute_partner_order(self):
        for picking in self:
            sale = False
            if not picking.sale_id:
                sale_orders = picking.purchase_id._get_sale_orders()
                if len(sale_orders):
                    sale = sale_orders[0]
            else:
                sale = picking.sale_id
            picking.partner_order_id = sale.partner_id if sale else False

    def _compute_total_gross_weight_print(self):
        for picking in self:
            picking.total_gross_weight_print = picking.total_gross_weight or picking.shipping_weight
