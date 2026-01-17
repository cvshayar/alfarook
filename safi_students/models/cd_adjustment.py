from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning, UserError, ValidationError


class CdAdjustment(models.Model):
    _name = 'cd.adjustment'
    _description = 'CD Adjustment'
    
    student_id = fields.Many2one('student.student')
    date = fields.Date(default=fields.Date.today)
    amount = fields.Float()
    due_id = fields.Many2one('student.fee.dues')
    refund_amount = fields.Float()
    initiate_refund = fields.Boolean(default=True)
    line_ids = fields.One2many('cd.adjustment.line', 'cd_adjustment_id')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft')
    
    @api.onchange('student_id')
    def load_line_ids(self): 
        self.line_ids = False
        if self.student_id:
            cd = self.env['student.fee.dues'].search([('fee_id.name', '=', 'CD'), ('student_id', '=', self.student_id.id)])
            self.amount = cd.paid_amount - cd.refund - cd.adjustment
            self.due_id = cd
            new_lines = self.env['cd.adjustment.line']
            dues = self.env['student.fee.dues'].search([('student_id', '=', self.student_id.id), ('balance', '>', 0)])
            for due in dues:
                data = {'fee_id': due.fee_id.id, 'amount': 0, 'academic_year': due.academic_year,
                        'semester_id': due.semester_id.id, 'due_id': due.id, 'balance': due.balance}
                new_line = new_lines.new(data)
                new_lines += new_line
            self.line_ids += new_lines
            self._adjust_cd_amount()
            self._cd_refund_amount()
            
    @api.onchange('amount')
    def onchange_amount(self):
        self._adjust_cd_amount()
        self._cd_refund_amount()
            
    def _adjust_cd_amount(self):
        balance_amount = self.amount
        for due in self.line_ids:
            amount = due.balance if due.balance <= balance_amount else balance_amount
            balance_amount -= amount
            due.amount = amount if amount > 0 else 0
            
    @api.onchange('line_ids')
    def _cd_refund_amount(self):
        self.refund_amount = self.amount - sum(self.line_ids.mapped('amount'))
        
    def get_refund_year(self, date):
        if date.strftime('%B') in ['January', 'February', 'March', 'April', 'May']:
            refund_year = date.year - 1
        else:
            refund_year = date.year
        return refund_year
                   
    @api.constrains('amount', 'line_ids')
    def check_amount(self):
        if sum(self.line_ids.mapped('amount')) > self.amount:
            raise ValidationError(str('Adjustment amount cannot exceed %s' % self.amount))
        
    def update_student_dues(self):
        if self.due_id:
            self.due_id.update({'refund': self.refund_amount, 'adjustment': sum(self.line_ids.mapped('amount'))})
            self.due_id.calculate_net_payable_amount()
        for each in self.line_ids.filtered(lambda x: x.amount > 0):
            paid_amount = each.due_id.paid_amount
            total_paid_amount = paid_amount + each.amount
            each.due_id.write({'paid_amount': total_paid_amount})
            each.due_id.calculate_net_payable_amount()
            
    def initiate_cd_refund(self):
        data = (0, 0, {'fee_id': self.due_id.fee_id.id,
                'collected_amount': self.due_id.paid_amount,
                'refund_amount': self.refund_amount,
                'academic_year': self.due_id.academic_year,
                'semester_id': self.student_id.semester_id.id,
                'due_id': self.due_id.id,
                'month_id': '',
                'year': ''
                })
        domain = [('student_id', '=', self.student_id.id), ('fee_line.fee_id.name', '=', 'CD'), ('state', '=', 'paid')]
        fee_collection = self.env['fee.collection'].search(domain)
        values = {
            'student_id': self.student_id.id,
            'refund_date': self.date,
            'fee_collection_id': fee_collection.id,
            'admission_number': self.student_id.admission_number,
            'payment_mode': '',
            'batch_id': self.student_id.batch_id.id,
            'refund_line': [data],
            'refund_year': self.get_refund_year(self.date), 
        }
        refund = self.env['fee.refund'].create(values)
        refund.onchange_refund_date()
        
            
    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.update_student_dues()
        if vals['refund_amount'] > 0 and vals['initiate_refund']:
            res.initiate_cd_refund()
        res.state = 'confirm'
        return res
                
        
    

class CdAdjustmentLine(models.Model):
    _name = 'cd.adjustment.line'
    _description = 'CD Adjustment Line'
    
    cd_adjustment_id = fields.Many2one('cd.adjustment')
    fee_id = fields.Many2one('fees.item')
    amount = fields.Float()
    month_id = fields.Many2one('calendar.month')
    year = fields.Integer()
    semester_id = fields.Many2one('semester.semester')
    academic_year = fields.Integer()
    due_id = fields.Many2one('student.fee.dues')
    balance = fields.Float()
