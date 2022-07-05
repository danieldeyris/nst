# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    incoterm_description = fields.Text("Incoterm Description")
    incoterm_is_additionnal_info = fields.Boolean(related="incoterm_id.is_additionnal_info")
    incoterm_full_name = fields.Char(compute="_compute_incoterm_full_name")

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.incoterm_description:
            res['incoterm_description'] = self.incoterm_description
        return res

    def _compute_incoterm_full_name(self):
        for order in self:
            if not order.incoterm_id:
                order.incoterm_full_name = False
            else:
                if order.incoterm_description:
                    order.incoterm_full_name = "\n".join([order.incoterm_id.code, order.incoterm_description])
                else:
                    order.incoterm_full_name = order.incoterm_id.code

    @api.onchange('incoterm_id', 'partner_id', 'partner_shipping_id', 'warehouse_id')
    def get_incoterm_description(self):
        for order in self:
            if not order.incoterm_id:
                order.incoterm_description = False
            else:
                order.incoterm_description = order.incoterm_id.get_additionnal_informations(order.partner_id, order.dest_address_id or order.picking_type_id.warehouse_id.partner_id)