from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('ready', 'Ready')], tracking=True)

    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'ready',
            'date_order': fields.Datetime.now()
        })
        return True

    def action_validation(self):
        result = super(SaleOrder, self).action_confirm()
        return result

    def action_cancel_validation(self):
        result = super(SaleOrder, self).action_cancel()
        return result

    @api.depends('state', 'order_line.invoice_status')
    def _get_invoice_status(self):
        unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done', 'ready'])
        unconfirmed_orders.invoice_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (d['order_id'][0], d['invoice_status'])
            for d in self.env['sale.order.line'].read_group([
                    ('order_id', 'in', confirmed_orders.ids),
                    ('is_downpayment', '=', False),
                    ('display_type', '=', False),
                ],
                ['order_id', 'invoice_status'],
                ['order_id', 'invoice_status'], lazy=False)]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state not in ('sale', 'done'):
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('state', 'price_reduce', 'product_id', 'untaxed_amount_invoiced', 'qty_delivered', 'product_uom_qty')
    def _compute_untaxed_amount_to_invoice(self):
        for line in self:
            if line.state == 'ready':
                amount_to_invoice = 0.0
                if line.state in ['sale', 'done', 'ready']:
                    # Note: do not use price_subtotal field as it returns zero when the ordered quantity is
                    # zero. It causes problem for expense line (e.i.: ordered qty = 0, deli qty = 4,
                    # price_unit = 20 ; subtotal is zero), but when you can invoice the line, you see an
                    # amount and not zero. Since we compute untaxed amount, we can use directly the price
                    # reduce (to include discount) without using `compute_all()` method on taxes.
                    price_subtotal = 0.0
                    uom_qty_to_consider = line.qty_delivered if line.product_id.invoice_policy == 'delivery' else line.product_uom_qty
                    price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    price_subtotal = price_reduce * uom_qty_to_consider
                    if len(line.tax_id.filtered(lambda tax: tax.price_include)) > 0:
                        # As included taxes are not excluded from the computed subtotal, `compute_all()` method
                        # has to be called to retrieve the subtotal without them.
                        # `price_reduce_taxexcl` cannot be used as it is computed from `price_subtotal` field. (see upper Note)
                        price_subtotal = line.tax_id.compute_all(
                            price_reduce,
                            currency=line.order_id.currency_id,
                            quantity=uom_qty_to_consider,
                            product=line.product_id,
                            partner=line.order_id.partner_shipping_id)['total_excluded']

                    if any(line.invoice_lines.mapped(lambda l: l.discount != line.discount)):
                        # In case of re-invoicing with different discount we try to calculate manually the
                        # remaining amount to invoice
                        amount = 0
                        for l in line.invoice_lines:
                            if len(l.tax_ids.filtered(lambda tax: tax.price_include)) > 0:
                                amount += l.tax_ids.compute_all(l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity)['total_excluded']
                            else:
                                amount += l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity

                        amount_to_invoice = max(price_subtotal - amount, 0)
                    else:
                        amount_to_invoice = price_subtotal - line.untaxed_amount_invoiced

                line.untaxed_amount_to_invoice = amount_to_invoice
            else:
                super(SaleOrderLine, line)._compute_untaxed_amount_to_invoice()
