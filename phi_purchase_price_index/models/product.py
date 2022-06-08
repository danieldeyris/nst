# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_price_index = fields.Boolean(string="Prix Achat Indiciaire", default=False)

    def update_price_index(self):
        #current_index = self._get_current_index()
        new_cost = 0
        vendors = self.seller_ids.mapped('name')
        self.seller_ids.filtered(lambda s: not s.is_first_price_index).unlink()
        for vendor in vendors:
            qty_done = []
            quantities = self.seller_ids.filtered(lambda s: s.name.id == vendor.id).mapped('min_qty')

            for min_qty in quantities:
                if min_qty not in qty_done:
                    qty_done.append(min_qty)
                    seller = self.seller_ids.filtered(lambda s: s.name.id == vendor.id and s.min_qty == min_qty and s.is_first_price_index)
                    if len(seller) > 1:
                        raise UserError(_('Vous ne pouvez pas avoir plusieurs prix avec une date de début vide pour un meme couple fournisseur/quantité minimale'))

                    if not seller.purchase_index_id:
                        seller.purchase_index_id = self.env["phi_purchase_price_index.purchase.index"]._get_current_index()

                    for index in self.env["phi_purchase_price_index.purchase.index"].search([('date_from', '>', seller.purchase_index_id.date_from)]).sorted(lambda t: t.date_from):
                        prices = index._calculate_price_index(seller)
                        seller_new = self.seller_ids.filtered(lambda s: s.name.id == vendor.id and s.min_qty == min_qty and s.purchase_index_id.id == index.id)
                        if not seller_new:
                            seller_new = seller.copy({
                                'purchase_index_id': index.id,
                                'price': prices.get("price"),
                                'date_start': index.date_from,
                                'date_end': False,
                                'portion_meps_price': prices.get("part_meps"),
                                'portion_mo_price': prices.get("part_mo"),
                                'portion_lme_price': prices.get("part_lme"),
                                'portion_meps': prices.get("portion_meps"),
                                'portion_mo': prices.get("portion_mo"),
                                'portion_lme': prices.get("portion_lme"),
                            })
                        else:
                            seller_new.write({
                                'price': prices.get("price"),
                                'date_start': index.date_from,
                                'date_end': False,
                                'portion_meps_price': prices.get("part_meps"),
                                'portion_mo_price': prices.get("part_mo"),
                                'portion_lme_price': prices.get("part_lme"),
                                'portion_meps': prices.get("portion_meps"),
                                'portion_mo': prices.get("portion_mo"),
                                'portion_lme': prices.get("portion_lme"),
                            })
                        if not seller.date_end or seller.date_end >= index.date_from:
                            seller.date_end = index.date_from - timedelta(days=1)
                        seller = seller_new

    def update_cost_index(self):
        for product in self.env["product.template"].search([('purchase_price_index', '=', True)]):
            product._compute_standard_price()


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    portion_meps = fields.Float(string="MEPS %", help="Pourcentage de matière premières", default=0, copy=True)
    portion_mo = fields.Float(string="MO %", help="Pourcentage de  main d'oeuvre", default=0, copy=True)
    portion_lme = fields.Float(string="LME %", help="Pourcentage de  traitement de surface", default=0, copy=True)

    portion_meps_price = fields.Float(string="MEPS", help="Prix de matière premières", default=0, copy=True)
    portion_mo_price = fields.Float(string="MO", help="prix de main d'oeuvre", default=0, copy=True)
    portion_lme_price = fields.Float(string="LME", help="Prix de traitement de surface", default=0, copy=True)

    purchase_price_index = fields.Boolean(related="product_tmpl_id.purchase_price_index", store=True)

    purchase_index_id = fields.Many2one('phi_purchase_price_index.purchase.index', string="Index Achat")

    is_first_price_index = fields.Boolean("First price index", compute="_compute_is_first_price_index")

    # _sql_constraints = [
    #     ('check_portions_total', 'check(portion_meps + portion_mo + portion_lme) >= 99 or not purchase_price_index)', 'Le total des indices doit être égal à 100'),
    # ]

    @api.onchange('portion_meps_price','portion_mo_price','portion_lme_price')
    def _onchange_portion_meps_price(self):
        for line in self:
            line.price = line.portion_meps_price + line.portion_mo_price + line.portion_lme_price
            if line.price:
                line.portion_meps = round(line.portion_meps_price / line.price * 100 , 2)
                line.portion_mo = round(line.portion_mo_price / line.price * 100, 2)
                line.portion_lme = round(line.portion_lme_price / line.price * 100, 2)
            else:
                line.portion_meps = 0
                line.portion_mo = 0
                line.portion_lme = 0

    @api.onchange('date_start')
    def _compute_is_first_price_index(self):
        for line in self:
            line.is_first_price_index = line.purchase_price_index and not line.date_start

    @api.model
    def create(self, vals):
        if vals.get("product_tmpl_id") and not vals.get("purchase_index_id"):
            product = self.env["product.template"].browse(vals["product_tmpl_id"])
            if product and product.purchase_price_index:
                date = None
                index = self.env["phi_purchase_price_index.purchase.index"]._get_current_index()
                if index:
                    vals["purchase_index_id"] = index.id
                else:
                    raise UserError(_('Aucun index validé trouvé'))

        res = super(SupplierInfo, self).create(vals)

        if res.purchase_price_index and not res.date_start:
            res.product_tmpl_id.update_price_index()

        return res

    def write(self, vals):
        res = super().write(vals)
        if 'price' in vals:
            if self.purchase_price_index and not self.date_start:
                self.update_price_index()
        return res

    def update_price_index(self):
        self.ensure_one()
        current_index = self
        for index in self.env["phi_purchase_price_index.purchase.index"].search([('date_from', '>', self.purchase_index_id.date_from)]).sorted(lambda t: t.date_from):
            seller = self.product_tmpl_id.seller_ids.filtered(lambda s: s.name.id == self.name.id  and s.min_qty == self.min_qty and s.purchase_index_id.id == index.id)
            if seller:
                prices = index._calculate_price_index(current_index)
                seller.price = prices.get("price")
                seller.portion_meps_price = prices.get("part_meps")
                seller.portion_mo_price = prices.get("part_mo")
                seller.portion_lme_price =prices.get("part_lme")
                seller.portion_meps = prices.get("portion_meps")
                seller.portion_mo = prices.get("portion_mo")
                seller.portion_lme = prices.get("portion_lme")
                current_index = seller

    # def unlink(self):
    #     for line in self:
    #         if line.purchase_price_index and line.date_start:
    #             raise UserError('Vous ne pouvez pas supprimer cet indice, supprimez le premier indice')
    #         if line.purchase_price_index and not line.date_start:
    #             line.product_tmpl_id.seller_ids.filtered(lambda s: s.name.id == line.name.id and s.min_qty == line.min_qty and s.purchase_index_id.id != line.purchase_index_id.id).unlink()
    #     res = super(SupplierInfo, self).unlink()