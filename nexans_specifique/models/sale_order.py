# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_price_index = fields.Many2one('phi_purchase_price_index.purchase.index', string='Indice Prix', compute="_computepurchase_price_index")
    indice_meps = fields.Date("Indice Meps")
    customer_text = fields.Text(string="Texte Client")
    product_attachment_nb = fields.Integer("Product Attachment #", compute="_compute_product_attachment_nb")

    @api.onchange('opportunity_id')
    def onchange_opportunity_id(self):
        for order in self:
            if order.opportunity_id:
                order.analytic_account_id = order.opportunity_id.account_analytic_id

    @api.model
    def create(self, vals):
        if vals.get('opportunity_id') and not vals.get('analytic_account_id'):
            lead = self.env['crm.lead'].browse(vals.get('opportunity_id'))
            if lead.account_analytic_id:
                vals['analytic_account_id'] = lead.account_analytic_id.id
        result = super(SaleOrder, self).create(vals)
        return result

    def _computepurchase_price_index(self):
        for order in self:
            order.purchase_price_index = self.env["phi_purchase_price_index.purchase.index"]._get_current_index(order.date_order)

    def _compute_product_attachment_nb(self):
        for order in self:
            products = order.mapped('order_line.product_id')
            attachments = self.env['ir.attachment'].search(
                [
                    '|', '&',
                    ('res_model', 'in', ['product.product']),
                    ('res_id', 'in', products.ids),'&',('res_model', 'in', ['product.template']),
                    ('res_id', 'in', products.mapped('product_tmpl_id').ids)
                ])
            order.product_attachment_nb = len(attachments)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'company_id', 'currency_id', 'product_uom')
    def _compute_purchase_price(self):
        for line in self:
            if line.product_id:
                if line.product_id.product_tmpl_id.purchase_price_index:
                    seller = line.product_id._select_seller(
                        quantity=line.product_qty,
                        date=line.order_id.date_order and line.order_id.date_order.date(),
                        uom_id=line.product_uom)
                    if seller:
                        product_cost = seller.price
                        if not product_cost:
                            if not line.purchase_price:
                                line.purchase_price = 0.0
                            continue
                        fro_cur = line.product_id.cost_currency_id
                        to_cur = line.currency_id or line.order_id.currency_id
                        if line.product_uom and line.product_uom != line.product_id.uom_id:
                            product_cost = line.product_id.uom_id._compute_price(
                                product_cost,
                                line.product_uom,
                            )
                        line.purchase_price = fro_cur._convert(
                            from_amount=product_cost,
                            to_currency=to_cur,
                            company=line.company_id or self.env.company,
                            date=line.order_id.date_order or fields.Date.today(),
                            round=False,
                        ) if to_cur and product_cost else product_cost
                else:
                    super(SaleOrderLine, line)._compute_purchase_price()
