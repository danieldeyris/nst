# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.addons.base.models.res_partner import WARNING_HELP, WARNING_MESSAGE


class Partner(models.Model):
    _inherit = 'res.partner'

    def init(self):
        partners = self.env["res.partner"].search([('property_stock_customer', '=', self.env.ref('stock.stock_location_customers').id)])
        for partner in partners:
            if partner.name:
                vals = {
                    "name": partner.name,
                    "location_id": self.env.ref('stock.stock_location_customers').id,
                    "usage": "customer",
                }
                location = self.env["stock.location"].create(vals)
                partner.property_stock_customer = location.id

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            # Create a location for the customer
            vals = {
                "name": val["name"],
                "location_id": self.env.ref('stock.stock_location_customers').id,
                "usage": "customer",
            }
            location = self.env["stock.location"].create(vals)
            val["property_stock_customer"] = location.id

        res = super(Partner, self).create(vals_list)
        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)
        if vals.get("name"):
            if self.property_stock_customer != self.env.ref('stock.stock_location_customers'):
                self.property_stock_customer.name = vals.get("name")
        return res
