# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.exceptions import UserError


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    def write(self, vals):
        try:
            res = super(PurchaseRequisitionLine, self).write(vals)
            if 'price_unit' in vals:
                # if vals['price_unit'] <= 0.0 and any(
                #         requisition.state not in ['draft', 'cancel', 'done'] and
                #         requisition.is_quantity_copy == 'none' for requisition in self.mapped('requisition_id')):
                    #raise UserError(_('You cannot confirm the blanket order without price.'))
                # If the price is updated, we have to update the related SupplierInfo
                if vals['price_unit'] > 0.0:
                    self.supplier_info_ids.write({'price': vals['price_unit']})
                return res
        except UserError:
            pass

        return False
