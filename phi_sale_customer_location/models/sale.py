# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_method = fields.Many2one('account.journal', string="Payment method", domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            self.payment_method = self.partner_id.payment_method
        return res

    @api.model
    def create(self, vals):
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if partner.payment_method.id and not vals.get('payment_method'):
            vals['payment_method'] = partner.payment_method.id
        result = super(SaleOrder, self).create(vals)
        return result

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.payment_method.id:
            invoice_vals['payment_method'] = self.payment_method.id
        return invoice_vals

