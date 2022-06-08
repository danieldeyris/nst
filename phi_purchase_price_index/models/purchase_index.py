# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class PurchaseIndex(models.Model):
    _name = 'phi_purchase_price_index.purchase.index'
    _description = 'indices'
    _order = "date_from desc"
    _rec_name = 'date_from'

    date_from = fields.Date(string="Date", required=True)
    index_meps = fields.Integer(string="MEPS", help="Indice matière premières", default=0, required=True)
    index_mo = fields.Integer(string="MO", help="Indice main d'oeuvre", default=0, required=True)
    index_lme = fields.Integer(string="LME", help="Indice traitement de surface", default=0, required=True)

    state = fields.Selection([('draft', 'Brouillon'), ('done', 'Traité')], 'Statut', readonly=True, copy=False, default='draft', required=True)
    display_name = fields.Char(compute='_compute_display_name')

    _sql_constraints = [
        ('unique_date', 'unique (date_from)', 'La date doit être unique')
    ]

    def update_products_prices(self):
        products_index = self.env["product.template"].search([('purchase_price_index', '=', True)])
        for product in products_index:
            product.update_price_index()

    @api.model
    def create(self, vals):
        res = super(PurchaseIndex, self).create(vals)
        self.update_products_prices()
        return res

    def unlink(self):
        res = super(PurchaseIndex, self).unlink()
        self.update_products_prices()
        return res

    def write(self, vals):
        result = super(PurchaseIndex, self).write(vals)
        self.update_products_prices()
        return result

    def copy(self, default=None):
        default = dict(default or {})
        last_index = self.env["phi_purchase_price_index.purchase.index"].search([],order='date_from desc', limit=1)
        default['date_from'] = last_index.date_from + timedelta(weeks=4)
        return super().copy(default)

    def _select_seller_for_index(self, product_id, date):
        res = self.env['product.supplierinfo']
        sellers = product_id.seller_ids.filtered(lambda s: s.name.active).sorted(lambda s: (s.sequence, -s.min_qty, s.price, s.id))
        sellers = sellers.filtered(lambda s: not s.company_id or s.company_id.id == self.env.company.id)
        for seller in sellers:
            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            res |= seller
        return res

    def _calculate_price_index(self, seller):
        if seller.purchase_index_id:
            return self._calculate_index_evolution(seller, self)
        else:
            return {
                'price': seller.price,
                'part_meps': 0,
                'part_mo': 0,
                'part_lme': 0,
                'portion_meps': 0,
                'portion_mo': 0,
                'portion_lme': 0,
            }

    @staticmethod
    def _calculate_index_evolution(seller_from, index_to, index_from=False):
        if not index_from:
            index_from = seller_from.purchase_index_id
        if not index_from or not index_to:
            return  {
                'price': seller_from.price,
                'part_meps': 0,
                'part_mo': 0,
                'part_lme': 0,
                'portion_meps': 0,
                'portion_mo': 0,
                'portion_lme': 0,
            }
        part_meps = seller_from.portion_meps_price * index_to.index_meps / index_from.index_meps if index_from.index_meps else 0
        part_mo = seller_from.portion_mo_price * index_to.index_mo / index_from.index_mo if index_from.index_mo else 0
        part_lme = seller_from.portion_lme_price * index_to.index_lme / index_from.index_lme if index_from.index_lme else 0

        price = part_meps + part_mo + part_lme

        if price:
            portion_meps = round(part_meps / price * 100, 2)
            portion_mo = round(part_mo / price * 100, 2)
            portion_lme = round(part_lme / price * 100, 2)
        else:
            portion_meps = 0
            portion_mo = 0
            portion_lme = 0

        ret = {
            'price': price,
            'part_meps': part_meps,
            'part_mo': part_mo,
            'part_lme': part_lme,
            'portion_meps': portion_meps,
            'portion_mo': portion_mo,
            'portion_lme': portion_lme,
        }
        return ret

    def _get_current_index(self, date=None):
        if date is None:
            date = fields.Date.context_today(self)
        return self.env["phi_purchase_price_index.purchase.index"].search([('date_from', '<=', date)], order='date_from desc', limit=1)

    def action_apply(self):
        index_draft = self.env["phi_purchase_price_index.purchase.index"].search([('state', '=', 'draft'),('date_from', '<', self.date_from)])
        if len(index_draft) > 0:
            raise UserError(_('Il existe un index en brouillon avec une date anterieure.'))
        current_index = self._get_current_index()
        products_index = self.env["product.template"].search([('purchase_price_index', '=', True)])
        for product in products_index:
            new_cost = 0
            sellers = self._select_seller_for_index(product, self.date_from)
            for seller in sellers:
                new_price = self._calculate_price_index(seller)
                seller.copy({
                    'purchase_index_id': self.id,
                    'price': new_price,
                    'date_start': self.date_from,
                    'date_end': False,
                })
                if not seller.date_end or seller.date_end >= self.date_from:
                    seller.date_end = self.date_from - timedelta(days=1)
                # Nouveau Cout
                if self.env.company.currency_id != seller.currency_id:
                    new_price = seller.currency_id._convert(new_price, self.env.company.currency_id, self.env.company, self.date_from)

                if seller.min_qty <= 1 and new_cost < new_price:
                    new_cost = new_price

            if new_cost and product.categ_id.property_cost_method == 'standard':
                if product.uom_id != product.uom_po_id:
                    new_cost = product.uom_po_id._compute_price(new_cost, product.uom_id)
                product.standard_price = new_cost

        self.state = 'done'

    def _compute_display_name(self):
        for index in self:
            index.display_name = "Date: %s - MEPS=%s, MO=%s, LME=%s" % (format_date(self.env, index.date_from), index.index_meps, index.index_mo, index.index_lme)
