# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError




class hr_expense_sheet(models.Model):
    _name = 'hr.expense.sheet'
    _inherit = 'hr.expense.sheet'

    disbursement_ids = fields.One2many('hr.expense.sheet.disbursement', 'sheet_id', string='Anticipo/Devuelta',
                                       states={'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)
    total_disbursement = fields.Float(string = "Total desembolsado", compute="_compute_total_disbursement")
    dif_total_disbursement = fields.Float('Diferencia', compute= '_compute_dif')
    state = fields.Selection([('submit', 'Submitted'),
                              ('approve', 'Approved'),
                              ('desembolsado', 'Desembolsado'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False,
                             default='submit', required=True,
                             help='Expense Report State')

    @api.one
    @api.constrains('disbursement_ids','state')
    def condiciones(self):

        if self.state == 'desembolsado':
            if self.total_disbursement <= 0:
                raise exceptions.ValidationError('Es necesario agregar un desembolso')
        if self.state =='post':
            if self.total_disbursement != self.total_amount:
                raise exceptions.ValidationError('El monto desembolsado ('+str(self.total_disbursement)+') debe ser igual al monto gastado ('+str(self.total_amount)+') para precentar asientos contables')

    @api.one
    @api.depends('total_disbursement','total_amount')
    def _compute_dif(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        self.dif_total_disbursement = self.total_disbursement - self.total_amount

    @api.multi
    def desembolsar_expense_sheets(self):
        self.write({'state': 'desembolsado', 'responsible_id': self.env.user.id})

    @api.one
    @api.depends('disbursement_ids', 'disbursement_ids.amount')
    def _compute_total_disbursement(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        total = 0

        for line in self.disbursement_ids:

            if line.type == u'ANT':
                total = total + line.amount
            else:
                total = total - line.amount

        self.total_disbursement = total

    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'desembolsado' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        res = self.mapped('expense_line_ids').action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode=='own_account':
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        return res


class hr_expense_sheet_disbursement(models.Model):
    _name = 'hr.expense.sheet.disbursement'
    _rec_name = 'description'
    _description = 'Dinero entregado'

    type = fields.Selection(string="Tipo", selection=[('ANT', 'Anticipo'), ('DEV', 'Devuelta'), ], required=True)
    description = fields.Char('Descripcion')
    amount = fields.Float('Cantidad', store=True)
    date_disbursement = fields.Datetime('Fecha del desembolso', readonly=True, index=True, copy=False, default=fields.Datetime.now, store=True)
    sheet_id = fields.Many2one('hr.expense.sheet',string="Expense Report", readonly=True, copy=False)
    type = fields.Selection(string="Tipo", selection=[('ANT', 'Anticipo'), ('DEV', 'Devuelta'), ], required=True)




