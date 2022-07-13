# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    weight_net = fields.Float("Weight", compute="_compute_weight_net", digits='Stock Weight')
    weight_gross = fields.Float("Weight Gross", digits='Stock Weight')
    weight_gross_print = fields.Float("Gross Weight", compute="_compute_weight_gross", digits='Stock Weight')
    sale_line = fields.Many2one(
        related="move_id.sale_line_id", readonly=True, string="Related order line"
    )
    currency_id = fields.Many2one(
        related="sale_line.currency_id", readonly=True, string="Sale Currency"
    )
    sale_price_unit = fields.Float(
        related="sale_line.price_unit", readonly=True, string="Sale price unit"
    )
    price_reduce = fields.Float(
        related="sale_line.price_reduce", readonly=True, string="Sale price unit"
    )

    sale_price_subtotal = fields.Monetary(
        compute="_compute_sale_order_line_fields",
        string="Price subtotal",
        compute_sudo=True,
    )

    def _compute_weight_gross(self):
        for line in self:
            line.weight_gross_print = line.weight_gross or line.weight_net

    def _compute_weight_net(self):
        for line in self:
            if line.product_id:
                line.weight_net = line.product_id.weight * line.qty_done

    def _get_aggregated_product_quantities(self, **kwargs):
        aggregated_move_lines = super(StockMoveLine, self)._get_aggregated_product_quantities(**kwargs)
        for move_line in self:
            name = move_line.product_id.display_name
            description = move_line.move_id.description_picking
            if description == name or description == move_line.product_id.name:
                description = False
            uom = move_line.product_uom_id
            line_key = str(move_line.product_id.id) + "_" + name + (description or "") + "uom " + str(uom.id)

            if aggregated_move_lines[line_key].get('weight') == None:
                aggregated_move_lines[line_key]['weight'] = move_line.weight_net
                aggregated_move_lines[line_key]['weight_gross'] = move_line.weight_gross_print
                aggregated_move_lines[line_key]['country'] = move_line.product_id.intrastat_origin_country_id.name
            else:
                aggregated_move_lines[line_key]['weight'] += move_line.weight_net
                aggregated_move_lines[line_key]['weight_gross'] += move_line.weight_gross_print
        return aggregated_move_lines

    def _compute_sale_order_line_fields(self):
        for line in self:
            quantity = line.qty_done or line.product_qty
            line.sale_price_subtotal = line.price_reduce * quantity