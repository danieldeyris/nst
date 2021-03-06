# © 2010-2012 Andy Lu <andy.lu@elico-corp.com> (Elico Corp)
# © 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2017 valentin vinagre  <valentin.vinagre@qubiq.es> (QubiQ)
# © 2020 Manuel Regidor  <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def create(self, vals):
        company = vals.get("company_id", False)
        if company:
            company = self.env["res.company"].browse(company)
        else:
            company = self.env.company
        if not company.keep_name_so:
            vals["name"] = self.env["ir.sequence"].next_by_code("purchase.quotation") or "/"
        return super(PurchaseOrder, self).create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default["name"] = "/"
        # if self.origin and self.origin != "":
        #     default["origin"] = self.origin + ", " + self.name
        # else:
        #     default["origin"] = self.name
        default["origin"] = False
        return super(PurchaseOrder, self).copy(default)

    def button_confirm(self):
        for order in self:
            if order.state in ("draft", "sent") and not order.company_id.keep_name_so:
                if order.origin and order.origin != "":
                    quo = order.origin + ", " + order.name
                else:
                    quo = order.name
                order.write(
                    {
                        "origin": quo,
                        "name": self.env["ir.sequence"].next_by_code("purchase.order"),
                    }
                )
        return super().button_confirm()
