from odoo import api, fields, models
from odoo import tools, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning, UserError, ValidationError
from math import ceil
import pytz


# from tkinter import *


class CalendarMonth(models.Model):
    _name = 'calendar.month'
    _description = 'CalendarMonth'
    _rec_name = 'value'

    key = fields.Char()
    value = fields.Char()


class FeesItems(models.Model):
    _name = 'fees.item'
    _description = 'Fee items'
    _order = 'sort_order'

    name = fields.Char('Fee items')
    payable = fields.Selection([('Government', 'Government'), ('University', 'University'), ('College', 'College')],
                               default='College')
    sort_order = fields.Integer()
    is_other_fee = fields.Boolean(default=False)
    is_visible = fields.Boolean()
    amount = fields.Integer()
    account_id = fields.Many2one('account.account')
    group_id = fields.Many2one('fees.group')


class FeesGroup(models.Model):
    _name = 'fees.group'
    _description = 'Fees Group'
    _order = 'name'

    name = fields.Char()
    payable = fields.Selection([('Government', 'Government'), ('University', 'University'), ('College', 'College')],
                               default='Government')


class FeeInstallment(models.Model):
    _name = 'fee.installment'
    _description = 'Fee Installment'

    name = fields.Char()


class ProgrammeFee(models.Model):
    _name = 'programme.fee'
    _description = 'Programme fee'

    programme_ids = fields.Many2many('programme.programme')
    academic_year = fields.Integer(default=fields.Date.today().year)
    # installment_id = fields.Many2one('fee.installment')
    year = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    programme_line = fields.One2many('programme.fee.line', 'programme_fee_id', copy=True)
    fee_category_ids = fields.Many2many('fee.category', copy=False)
    total = fields.Integer(compute='compute_total', store=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft')
    semester_id = fields.Many2one('semester.semester')

    def confirm_programme_fee(self):
        self.state = 'confirmed'
        if len(self.env['programme.fee'].search(
                [('programme_ids', 'in', self.programme_ids.ids), ('academic_year', '=', self.academic_year),
                 ('semester_id', '=', self.semester_id.id),
                 ('year', '=', self.year), ('fee_category_ids', 'in', self.fee_category_ids.ids)])) > 1:
            raise UserError(str('Already configured'))

    @api.depends('programme_line')
    def compute_total(self):
        for rec in self:
            rec.total = sum(self.env['programme.fee.line'].search([('programme_fee_id', '=', rec.id)]).mapped('amount'))

    @api.onchange('semester_id')
    def onchange_method(self):
        if self.semester_id:
            year = int(self.semester_id.name) / 2
            self.year = str(ceil(year))

    @api.onchange('academic_year')
    def compute_programme_line(self):
        self.programme_line = False
        new_lines = self.env['programme.fee.line']
        for fee in self.env['fees.item'].search([]):
            data = {'fee_id': fee.id}
            new_line = new_lines.new(data)
            new_lines += new_line
        self.programme_line += new_lines


class ProgrammeFeeLine(models.Model):
    _name = 'programme.fee.line'
    _description = 'Programme fee line'

    programme_fee_id = fields.Many2one('programme.fee', ondelete='cascade')
    amount = fields.Float()
    fee_id = fields.Many2one('fees.item')


class FeeSchedule(models.Model):
    _name = 'fee.schedule'
    _description = 'Fee Schedule'

    academic_year = fields.Integer(default=fields.Datetime.now().year)
    # installment_id = fields.Many2one('fee.installment')
    year = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    semester_id = fields.Many2one('semester.semester')
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG')])
    start_date = fields.Date()
    end_date = fields.Date()
    first_fine = fields.Date('1st Fine Date')
    second_fine = fields.Date('2nd Fine Date')
    third_fine = fields.Date('3rd Fine Date')
    first_fine_amount = fields.Float('1st Fine Amount')
    second_fine_amount = fields.Float('2nd Fine Amount')
    third_fine_amount = fields.Float('3rd Fine Amount')

    @api.onchange('semester_id')
    def onchange_method(self):
        if self.semester_id:
            year = int(self.semester_id.name) / 2
            self.year = str(ceil(year))


class FeeCollection(models.Model):
    _name = 'fee.collection'
    _description = 'Fee Collection'
    _order = 'payment_year DESC, id DESC'

    name = fields.Char('Receipt number')
    student_id = fields.Many2one('student.student')
    academic_year = fields.Integer(group_operator=False)
    # installment_ids = fields.Many2many('fee.installment', default=get_default_installment)
    payment_date = fields.Date(default=fields.Date.today)
    batch_id = fields.Many2one('batch.batch')
    payment_year = fields.Integer()
    admission_number = fields.Integer()
    fee_type = fields.Selection([('student', 'Student'), ('other', 'Other')])
    paid_by = fields.Char()
    purpose = fields.Text()
    remarks = fields.Text()
    fee_line = fields.One2many('fee.collection.line', 'fee_collection_id')
    year = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    total = fields.Float(compute='compute_total', store=True)
    state = fields.Selection([('challan', 'Challan'), ('paid', 'Paid'), ('post', 'Posted'), ('cancelled', 'Cancelled')])
    application_number = fields.Char()
    is_refund = fields.Boolean()
    is_additional_fee = fields.Boolean()
    fee_category_id = fields.Many2one('fee.category')
    receipt_mode = fields.Selection([('Cash', 'Cash'), ('Bank', 'Bank'), ('Card', 'Card'), ('Cheque', 'Cheque'), ('Online', 'Online')],
                                    default='Cash')
    image1 = fields.Binary(compute='get_image')
    semester_id = fields.Many2one('semester.semester')
    filter_semester_id = fields.Many2one('semester.semester', store=False)
    filter_academic_year = fields.Integer(store=False)
    transaction_ref = fields.Char()
    bank = fields.Char()
    cheque_no = fields.Char()
    cheque_date = fields.Date()
    cheque_issued_bank = fields.Char()
    cheque_issued_branch = fields.Char()
    card_owner = fields.Char()
    card_no = fields.Char()
    dues_pending = fields.Text(compute='_compute_pending_dues')
    check_all = fields.Boolean()
    payment_history = fields.Html(store=False)

    @api.model
    def create(self, values):
        values['state'] = 'paid'
        sequence = self.env['fee.collection'].search(
            [('state', '!=', 'draft'), ('payment_year', '=', values['payment_year'])]).mapped('name')
        k = []
        if sequence:
            for i in sequence:
                k.append(int(i.split('/')[0]))
            k.sort()
        else:
            k = [1]
        # fee = self.env['fee.collection'].search([('name', '=', str(k[-1]) + '/' + str(values['payment_year']))])
        if sequence:
            values['name'] = str(int(k[-1]) + 1) + '/' + str(values['payment_year'])
        else:
            values['name'] = '1' + '/' + str(values['payment_year'])
        if values['fee_type'] == 'student':
            # semester = self.env['semester.semester'].browse([values['semester_id']])
            # previous_dues = self.env['student.fee.dues'].search(
            #     [('student_id', '=', values['student_id']), ('balance', '>', 0)]).filtered(
            #     lambda x: int(x.semester_id.name) < int(semester.name))
            # if previous_dues:
            #     raise UserError(
            #         _('Student has fee pending in semesters %s' % ','.join(previous_dues.mapped('semester_id.name'))))
            student = self.env['student.student'].browse([values['student_id']])
            if student.admission_number == 0:
                last_admission_no = self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('self_finance', '=', student.self_finance)],
                    order='admission_number DESC', limit=1)
                student.sudo().write({'admission_number': last_admission_no.admission_number + 1,
                                      'date_of_admission': values['payment_date']})
                if student:
                    values['admission_number'] = last_admission_no.admission_number + 1
        res = super(FeeCollection, self).create(values)
        if values['fee_type'] == 'student':
            res.update_student_dues()
        # res.post_payment()
        return res

    @api.onchange('payment_date')
    def onchange_payment_date(self):
        if self.payment_date.strftime('%B') in ['January', 'February', 'March', 'April', 'May']:
            self.payment_year = self.payment_date.year - 1
            self.academic_year = self.payment_date.year - 1
        else:
            self.payment_year = self.payment_date.year
            self.academic_year = self.payment_date.year

    @api.depends('student_id')
    def _compute_pending_dues(self):
        for each in self:
            each.dues_pending = ''
            if each.student_id:
                pending_dues = self.env['student.fee.dues'].search(
                    [('student_id', '=', each.student_id.id), ('balance', '>', 0)])
                semesters = pending_dues.mapped('semester_id')
                text = ''
                for semester in semesters:
                    amount = sum(pending_dues.filtered(lambda x: x.semester_id.id == semester.id).mapped('balance'))
                    text = text + 'Semester : %s    Amount : %s \n' % (semester.name, amount)
                each.dues_pending = text

    def unlink(self):
        for each in self:
            if each.state in ('paid', 'cancelled'):
                raise UserError(str('You are not allowed to delete receipt'))
            return super(FeeCollection, self).unlink()

    # def cancel_receipt(self):
    #     for each in self.fee_line:
    #         fee_dues = self.env['student.fee.dues'].search(
    #             [('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id),
    #              ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id)])
    #         if fee_dues:
    #             fee_dues.update({'paid_amount': fee_dues.paid_amount - each.amount})
    #             fee_dues.calculate_net_payable_amount()
    #     self.state = 'cancelled'
    
    def cancel_receipt(self):
        for each in self.fee_line:
            if each.due_id:
                each.due_id.update({'paid_amount': each.due_id.paid_amount - each.amount})
                each.due_id.calculate_net_payable_amount()
            else:
                if each.fee_id.id in [11, 12, 13, 14]:
                    fee_dues = self.env['student.fee.dues'].search(
                        [('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id),
                         ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id),
                         ('month_id', '=', each.month_id.id), ('year', '=', each.year)])
                else:
                    fee_dues = self.env['student.fee.dues'].search(
                        [('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id),
                         ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id),
                         ('month_id', '=', each.month_id.id), ('year', '=', each.year if each.year else False)])
                if fee_dues:
                    fee_dues.update({'paid_amount': fee_dues.paid_amount - each.amount})
                    fee_dues.calculate_net_payable_amount()
        self.state = 'cancelled'

    def compute_amount_total_words(self, amount):
        currency = self.env['res.currency'].search([('name', '=', 'INR')])
        return currency.amount_to_text(amount)

    def approve_payment(self):
        sequence = self.env['fee.collection'].search([('state', '=', 'paid')]).mapped('name')
        k = []
        for i in sequence:
            k.append(int(i.split('/')[0]))
        k.sort()
        if sequence:
            self.name = str(int(k[-1]) + 2) + '/' + str(fields.Date.year)
        else:
            self.name = '1' + '/' + str(fields.Date.year)
        if self.student_id.admission_number == 0:
            last_admission_no = self.env['student.student'].search(
                ['|', ('active', '=', True), ('active', '=', False),
                 ('self_finance', '=', self.student_id.self_finance)],
                order='admission_number DESC', limit=1)
            self.student_id.write({'admission_number': last_admission_no.admission_number + 1})
        self.state = 'paid'

    # @api.depends('bank_payment', 'total')
    # def compute_balance_payment(self):
    #     for each in self:
    #         each.balance_amount = sum(each.fee_line.mapped('amount')) - each.bank_payment

    @api.depends('student_id')
    def get_image(self):
        for each in self:
            each.image1 = each.student_id.image
            
    @api.onchange('fee_line')
    def check_all_items(self):
        if self.fee_line:
            if False in self.fee_line.mapped('checked'):
                self.check_all = False
            else:
                self.check_all = True
            for each in self.fee_line:
                each.checking_bool = True

    @api.onchange('check_all')
    def check_uncheck_line_ids(self):
        if self.fee_line:
            for each in self.fee_line.filtered(lambda x:x.is_readonly == False):
                if not each.checking_bool:
                    if self.check_all:
                        each.checked = True
                        each.get_amount()
                    if not self.check_all:
                        each.checked = False
                        each.get_amount()


    @api.depends('fee_line')
    def compute_total(self):
        for rec in self:
            for order in rec.fee_line:
                rec.total += order.amount

    # @api.onchange('fee_type', 'student_id', 'academic_year', 'year', 'payment_date',
    #               'application_number', 'semester_id')
    # def onchange_installment(self):
    #     if self.student_id:
    #         if not self.semester_id:
    #             self.semester_id = self.student_id.semester_id
    #         else:
    #             year = int(self.semester_id.name) / 2
    #             self.year = str(ceil(year))
    #         self.admission_number = self.student_id.admission_number
    #         self.batch_id = self.student_id.batch_id
    #         self.application_number = self.student_id.app_no
    #         self.fee_category_id = self.student_id.fee_category_id
    #         bank_payment = 0
    #     self.fee_line = False
    #     new_lines = self.env['fee.collection.line']
    #     if self.fee_type == 'student':
    #         fees = self.env['student.fee.dues'].search(
    #             [('academic_year', '=', self.academic_year), ('student_id', '=', self.student_id.id),
    #              ('semester_id', '=', self.semester_id.id)])
    #     if self.fee_type == 'student':
    #         for fee in fees:
    #             if fee.balance > 0:
    #                 data = {'fee_id': fee.fee_id.id, 'amount': fee.balance}
    #                 new_line = new_lines.new(data)
    #                 new_lines += new_line
    #         self.fee_line += new_lines
    #         if not fees:
    #             fee_items = self.env['fees.item'].search([('is_other_fee', '=', False), ('name', '!=', 'Fine')],
    #                                                      order='sort_order,name')
    #             for fee in fee_items:
    #                 data = {'fee_id': fee.id, 'amount': 0}
    #                 new_line = new_lines.new(data)
    #                 new_lines += new_line
    #             self.fee_line += new_lines
    
    @api.onchange('fee_type', 'student_id', 'filter_academic_year', 'year', 'payment_date',
                  'application_number', 'filter_semester_id', 'month')
    def onchange_installment(self):
        if self.student_id:
            self.admission_number = self.student_id.admission_number
            self.batch_id = self.student_id.batch_id
            self.application_number = self.student_id.app_no
            self.fee_category_id = self.student_id.fee_category_id
            self.semester_id = self.student_id.semester_id.id
        self.fee_line = False
        new_lines = self.env['fee.collection.line']
        if self.fee_type == 'student' and self.student_id:
            total_fees = self.env['student.fee.dues'].search([('student_id', '=', self.student_id.id)])
            academic_years = list(set(total_fees.mapped('academic_year')))
            string = '<table class="table table-bordered"><tr><th>SI No</th><th>Academic Year</th><th>Total Payable</th><th>Total Scholarship</th><th>Total Discount</th><th>Total Paid</th><th>Balance</th>'
            i = 0
            for academic_year in academic_years:
                i += 1
                total_payable = sum(total_fees.filtered(lambda x:x.academic_year == academic_year).mapped('gross_payable_amount'))
                total_scholarship = sum(total_fees.filtered(lambda x:x.academic_year == academic_year).mapped('scholarship_amount'))
                total_discount = sum(total_fees.filtered(lambda x:x.academic_year == academic_year).mapped('discount_amount'))
                total_paid = sum(total_fees.filtered(lambda x:x.academic_year == academic_year).mapped('paid_amount'))
                total_balance = sum(total_fees.filtered(lambda x:x.academic_year == academic_year).mapped('balance'))
                string = string + '<tr><td>%s</td><td>%s</td><td class="text-right">%s</td><td class="text-right">%s</td><td class="text-right">%s</td><td class="text-right">%s</td><td class="text-right">%s</td></tr>' % (i, academic_year, total_payable, total_scholarship, total_discount, total_paid, total_balance)
            self.payment_history = string + '</table>'
            domain = [('student_id', '=', self.student_id.id)]
            if self.filter_semester_id:
                domain.append(('semester_id', '=', self.filter_semester_id.id))
            if self.filter_academic_year:
                domain.append(('academic_year', '=', self.filter_academic_year))
            fees = self.env['student.fee.dues'].search(domain)
            for fee in fees:
                if fee.paid_amount == fee.net_payable_amount and fee.net_payable_amount > 0:
                    readonly = True
                else:
                    readonly = False
                if fee.net_payable_amount > 0:
                    data = {'fee_id': fee.fee_id.id, 'amount': fee.balance, 'is_readonly': readonly,
                            'academic_year': fee.academic_year, 'semester_id': fee.semester_id.id,
                            'due_id': fee.id, 'checked': False if readonly == True else True, 'paid_amount': fee.paid_amount, 'fee_amount': fee.net_payable_amount}
                    new_line = new_lines.new(data)
                    new_lines += new_line
            self.fee_line += new_lines
            new_line = []
            new_lines = self.env['fee.collection.line']
            if sum(fees.filtered(lambda x: x.fee_id.name == 'Tuition Fee').mapped('balance')) > 0:
                fine_items = self.env['student.fee.dues'].search([('fee_id.name', '=', 'Fine'), ('student_id', '=', self.student_id.id), ('semester_id', 'in', fees.filtered(lambda x: x.balance > 0 and x.fee_id.name == 'Tuition Fee').mapped('semester_id.id'))])
                for fine_item in fine_items.filtered(lambda x: x.balance == 0 and x.gross_payable_amount == 0):
                    fine_schedule = self.env['fee.schedule'].search([('academic_year', '=', fine_item.academic_year), ('semester_id', '=', fine_item.semester_id.id)
                                                                     , ('fine_date', '<=', self.payment_date)])
                    if fine_schedule:
                        if fine_schedule.fine_date == self.payment_date:
                            fine_amount = fine_schedule.fine_amount
                        else:
                            days = (self.payment_date - fine_schedule.fine_date).days
                            fine_amount = fine_schedule.fine_amount + (days * 10)
                    else:
                        fine_amount = 0
                    data = {'fee_id': fine_item.fee_id.id, 'academic_year': fine_item.academic_year, 
                            'semester_id': fine_item.semester_id.id, 'due_id': fine_item.id, 'fee_amount': fine_amount}
                    new_line = new_lines.new(data)
                    new_lines += new_line
                self.fee_line += new_lines
                
    def cancel_fee_receipt(self):
        form_view = self.env.ref('safi_students.fee_cancellation_view_form')
        return {
            'name': _('Cancellation'),
            'res_model': 'fee.cancellation',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_fee_collection_id': self.id,
                        'default_cancellation_date': fields.Date.today()}
        }

    # @api.constrains('student_id', 'semester_id')
    # def _check_fee_status(self):
    #     if self.student_id:
    #         previous_dues = self.env['student.fee.dues'].search(
    #             [('student_id', '=', self.student_id.id), ('balance', '>', 0)]).filtered(
    #             lambda x: int(x.semester_id.name) < int(self.semester_id.name))
    #         if previous_dues:
    #             raise UserError(
    #                 _('Student has fee pending in semesters %s' % ','.join(previous_dues.mapped('semester_id.name'))))
    #     fees = self.env['student.fee.dues'].search(
    #         [('academic_year', '=', self.academic_year), ('student_id', '=', self.student_id.id),
    #          ('semester_id', '=', self.semester_id.id)])
    #     if sum(fees.mapped('balance')) == 0 and sum(fees.mapped('net_payable_amount')) > 0 and self.student_id:
    #         raise UserError(str('Fully Paid'))
    
    @api.constrains('student_id')
    def check_fee_payment_status(self):
        if self.fee_type == 'student' and self.student_id:
            fees = self.env['student.fee.dues'].search([('student_id', '=', self.student_id.id)])
            if sum(fees.mapped('balance')) == 0 and sum(fees.mapped('net_payable_amount')) > 0 and self.student_id:
                raise UserError(str('Fully Paid'))

    def refund_fee(self):
        form_view = self.env.ref('safi_students.fee_refund_form')
        return {
            'name': _('Refund'),
            'res_model': 'fee.refund',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_fee_collection_id': self.id,
                        'default_refund_date': fields.Date.today()}
        }

    # def update_student_dues(self):
    #     for each in self.fee_line:
    #         fee_dues = self.env['student.fee.dues'].search(
    #             [('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id),
    #              ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id)])
    #         if fee_dues:
    #             fee_dues.update({'paid_amount': fee_dues.paid_amount + each.amount})
    #             fee_dues.calculate_net_payable_amount()
    #         else:
    #             values = {
    #                 'academic_year': self.academic_year,
    #                 'semester_id': self.semester_id.id,
    #                 'student_id': self.student_id.id,
    #                 'fee_id': each.fee_id.id,
    #                 'paid_amount': each.amount,
    #                 'gross_payable_amount': each.amount,
    #                 'net_payable_amount': each.amount
    #             }
    #             dues = self.env['student.fee.dues'].create(values)
    #             dues.calculate_net_payable_amount()
    
    def update_student_dues(self):
        if self.fee_type == 'student':
            for each in self.fee_line:
                if each.checked:
                    if each.due_id:
                        paid_amount = each.due_id.paid_amount
                        total_paid_amount = paid_amount + each.amount
                        each.due_id.write({'paid_amount': total_paid_amount})
                        each.due_id.calculate_net_payable_amount()
                    else:
                        # if each.fee_id.id in [11, 13, 12, 14]:
                        #     fee_dues = self.env['student.fee.dues'].search(
                        #         [('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id),
                        #          ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id)])
                        # else:
                        fee_dues = self.env['student.fee.dues'].search(
                            [('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id),
                             ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id)])

                        paid_amount = fee_dues.paid_amount
                        total_paid_amount = paid_amount + each.amount
                        fee_dues.write({'paid_amount': total_paid_amount})
                        fee_dues.calculate_net_payable_amount()
        else:
            for each in self.fee_line:
                if each.checked:
                    fee_dues = self.env['student.fee.dues'].search(
                        [('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id),
                         ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id)])
                    if fee_dues:
                        fee_dues.update({'paid_amount': fee_dues.paid_amount + each.amount})
                        fee_dues.calculate_net_payable_amount()
                    else:
                        values = {
                            'academic_year': self.academic_year,
                            'semester_id': self.semester_id.id,
                            'student_id': self.student_id.id,
                            'fee_id': each.fee_id.id,
                            'paid_amount': each.amount,
                            'gross_payable_amount': each.amount,
                            'net_payable_amount': each.amount,
                            'month': self.month
                        }
                        dues = self.env['student.fee.dues'].create(values)
                        dues.calculate_net_payable_amount()

    def post_payment(self):
        account_journal = self.env['account.journal'].search([('name', '=', self.receipt_mode)])
        move_line_values = []
        for each in self.fee_line:
            data = (0, 0, {
                'account_id': each.fee_id.account_id.id,
                'credit': each.amount,
                'date': self.payment_date,
                'debit': 0.0
            })
            move_line_values.append(data)
        data = (0, 0, {
            'account_id': account_journal.default_debit_account_id.id,
            'debit': sum(self.fee_line.mapped('amount')),
            'date': self.payment_date,
            'credit': 0.0
        })
        move_line_values.append(data)
        values = {
            'ref': self.name,
            'date': self.payment_date,
            'journal_id': account_journal.id,
            'company_id': self.env.user.company_id.id,
            'fee_id': self.id,
            'line_ids': move_line_values,
            'state': 'draft',
            'narration': str(self.student_id.admission_number) + ' ' + self.student_id.name
        }
        account_move = self.env['account.move'].create(values)
        account_move.action_post()
        self.state = 'post'
        
    @api.constrains('fee_line', 'total')
    def calculate_total_amount(self):
        if sum(self.fee_line.mapped('amount')) == 0 or self.total == 0:
            raise ValidationError('Amount to be collected should not be zero')


class FeeCollectionLine(models.Model):
    _name = 'fee.collection.line'
    _description = 'Fee Collection Line'

    fee_id = fields.Many2one('fees.item')
    fee_collection_id = fields.Many2one('fee.collection')
    amount = fields.Float()
    advance_amount = fields.Float()
    receipt_mode = fields.Selection([('Cash', 'Cash'), ('Bank', 'Bank'), ('Card', 'Card'), ('Cheque', 'Cheque'), ('Online', 'Online')],
                                    related='fee_collection_id.receipt_mode', store=True)
    month_id = fields.Many2one('calendar.month')
    year = fields.Integer()
    semester_id = fields.Many2one('semester.semester')
    academic_year = fields.Integer()
    due_id = fields.Many2one('student.fee.dues')
    checked = fields.Boolean()
    checking_bool = fields.Boolean(default=False)
    fee_amount = fields.Float()
    paid_amount = fields.Float()
    is_readonly = fields.Boolean(default=False)
    
    @api.onchange('checked')
    def get_amount(self):
        if self.checked:
            if self.fee_id.name == 'Fine':
                fine_schedule = self.env['fee.schedule'].search([('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id)
                                                                     , ('fine_date', '<=', self.fee_collection_id.payment_date)])
                if fine_schedule:
                    if fine_schedule.fine_date == self.fee_collection_id.payment_date:
                        self.amount = fine_schedule.fine_amount
                    else:
                        days = (self.fee_collection_id.payment_date - fine_schedule.fine_date).days
                        self.amount = fine_schedule.fine_amount + (days * 10)
                else:
                    self.amount = self.due_id.balance
            else:
                self.amount = self.due_id.balance
        else:
            self.amount = 0

    @api.model
    def create(self, values):
        # Add code here
        vals = {}
        if values['amount'] > 0 and values['checked']:
            vals = {
                'fee_id': values['fee_id'],
                # 'month_id': values['month_id'],
                # 'year': values['year'],
                'fee_collection_id': values['fee_collection_id'],
                'amount': values['amount'],
                'due_id': values['due_id'],
                'semester_id': values['semester_id'],
                'academic_year': values['academic_year'],
                'checked': values['checked'],
                'fee_amount': values['fee_amount'],
                'paid_amount': values['paid_amount'],
                'is_readonly': values['is_readonly']
            }
        return super(FeeCollectionLine, self).create(vals)


class RefundFee(models.Model):
    _name = 'fee.refund'
    _description = 'Refund Fee'
    _order = 'id DESC'

    # @api.model
    # def get_refund_authority(self):
    #     if self.user_has_groups('safi_students.group_self_user'):
    #         refunded_by = 'self_finance'
    #     else:
    #         refunded_by = 'aided'
    #     return refunded_by

    name = fields.Char('Refund Number')
    fee_collection_id = fields.Many2one('fee.collection')
    refund_date = fields.Date(default=fields.Date.today)
    refund_line = fields.One2many('fee.refund.line', 'fee_refund_id')
    state = fields.Selection([('draft', 'Waiting for Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'),
                              ('refund', 'Refunded'), ('post', 'Post'), ('to_cancel', 'Submitted for Cancellation'),
                              ('cancelled', 'Cancelled')])
    fee_type = fields.Selection([('student', 'Student'), ('other', 'Other')])
    batch_id = fields.Many2one('batch.batch')
    # refunded_by = fields.Selection([('aided', 'Aided'), ('self_finance', 'Self Finance')], default=get_refund_authority)
    admission_number = fields.Integer()
    student_id = fields.Many2one('student.student')
    refund_year = fields.Integer()
    payment_mode = fields.Selection([('Cash', 'Cash'), ('Bank', 'Bank'), ('Card', 'Card'), ('Cheque', 'Cheque')],
                                    default='Cash')
    transaction_ref = fields.Char()
    bank = fields.Char()
    cheque_no = fields.Char()
    cheque_date = fields.Date()
    cheque_issued_bank = fields.Char()
    cheque_issued_branch = fields.Char()
    card_owner = fields.Char()
    card_no = fields.Char()
    remarks = fields.Text()
    total = fields.Float(compute='compute_total')

    def unlink(self):
        for each in self:
            if each.state not in 'rejected':
                raise UserError(str('You are not allowed to delete before rejecting Refund receipt'))
        return super(RefundFee, self).unlink()

    @api.depends('refund_line')
    def compute_total(self):
        for rec in self:
            rec.total = 0
            for order in rec.refund_line:
                rec.total += order.refund_amount

    def cancel_receipt(self):
        for each in self.refund_line:
            if each.due_id:
                each.due_id.update({'refund': each.due_id.refund - each.refund_amount})
                each.due_id.calculate_net_payable_amount()
            else:
                fee_dues = self.env['student.fee.dues'].search(
                    [('semester_id', '=', self.fee_collection_id.semester_id.id),
                     ('student_id', '=', self.student_id.id), ('fee_id', '=', each.fee_id.id)])
                if fee_dues:
                    fee_dues.update({'refund': fee_dues.refund - each.refund_amount})
                    fee_dues.calculate_net_payable_amount()
        self.state = 'cancelled'

    @api.onchange('refund_date')
    def onchange_refund_date(self):
        if self.refund_date.strftime('%B') in ['January', 'February', 'March', 'April', 'May']:
            self.refund_year = self.refund_date.year - 1
        else:
            self.refund_year = self.refund_date.year

    def approve_receipt(self):
        refunded = self.env['fee.refund'].search(
            [('fee_collection_id', '=', self.fee_collection_id.id), ('state', '=', 'refund')])
        refunded = refunded.mapped('refund_line')
        for refund_fee in self.refund_line:
            refunded_amount = 0
            for each in refunded:
                refunded_amount += sum(
                    each.filtered(lambda x: x.fee_id.id == refund_fee.fee_id.id).mapped('refund_amount'))
            if refund_fee.refund_amount + refunded_amount > refund_fee.collected_amount:
                raise UserError(_('Refund amount for %s is greater than collected amount. Already refunded is %.2f' % (
                    refund_fee.fee_id.name, refunded_amount)))
            if refund_fee.refund_amount > refund_fee.collected_amount:
                raise ValidationError(
                    _('Refund amount of %s is greater than paid amount') % (refund_fee.fee_id.name.upper()))
        if self.state == 'draft':
            self.state = 'approved'
        else:
            self.state = 'cancelled'
            self.fee_collection_id.is_refund = False

    def update_student_dues(self):
        for each in self.refund_line:
            if each.due_id:
                each.due_id.update({'refund': each.refund_amount})
                each.due_id.calculate_net_payable_amount()
            else:
                fee_dues = self.env['student.fee.dues'].search(
                    [('semester_id', '=', each.semester_id.id),
                     ('student_id', '=', each.fee_refund_id.fee_collection_id.student_id.id),
                     ('fee_id', '=', each.fee_id.id), ('academic_year', '=', each.academic_year)])
                fee_dues.update({'refund': each.refund_amount})
                fee_dues.calculate_net_payable_amount()

    def post_payment(self):
        account_journal = self.env['account.journal'].search([('name', '=', self.fee_collection_id.receipt_mode)])
        move_line_values = []
        for each in self.refund_line:
            data = (0, 0, {
                'account_id': each.fee_id.account_id.id,
                'debit': each.refund_amount,
                'date': self.refund_date,
                'credit': 0.0
            })
            move_line_values.append(data)
        data = (0, 0, {
            'account_id': account_journal.default_debit_account_id.id,
            'credit': sum(self.refund_line.mapped('refund_amount')),
            'date': self.refund_date,
            'debit': 0.0
        })
        move_line_values.append(data)
        values = {
            'ref': self.name,
            'date': self.refund_date,
            'journal_id': account_journal.id,
            'company_id': self.env.user.company_id.id,
            'fee_id': self.id,
            'line_ids': move_line_values,
            'state': 'draft',
            'narration': 'Refund of %s %s %s' % (
                self.fee_collection_id.name, self.student_id.admission_number, self.student_id.name)
        }
        account_move = self.env['account.move'].create(values)
        account_move.action_post()
        self.state = 'post'

    def reject_receipt(self):
        if self.state == 'draft':
            self.state = 'rejected'
        else:
            self.state = 'refund'

    def compute_amount_total_words(self, amount):
        currency = self.env['res.currency'].search([('name', '=', 'INR')])
        return currency.amount_to_text(amount)

    @api.model
    def create(self, values):
        if self.env['fee.refund'].search([('fee_collection_id', '=', values['fee_collection_id']),
                                          ('state', '=', 'draft')]):
            raise UserError(_('Refund is already in Waiting for Approval state'))
        sequence = self.env['fee.refund'].search(
            [('state', 'in', ('refund', 'cancelled')), ('refund_year', '=', values['refund_year'])], order='id DESC',
            limit=1)
        if sequence:
            values['name'] = str(int(sequence.name.split('/')[0]) + 1) + '/' + str(values['refund_year'])
        else:
            values['name'] = '1' + '/' + str(values['refund_year'])
        res = super(RefundFee, self).create(values)
        res.approve_receipt()
        res.update_student_dues()
        res.refund_receipt()
        return res

    def refund_receipt(self):
        # sequence = self.env['fee.refund'].search([('state', 'in', ('post', 'refund', 'cancelled'))], order='id DESC',
        #                                          limit=1)
        # if sequence:
        #     self.name = str(int(sequence.name.split('/')[0]) + 1) + '/' + str(fields.Date.today().year)
        # else:
        #     self.name = '1' + '/' + str(fields.Date.today().year)
        self.fee_collection_id.is_refund = True
        self.state = 'refund'
        # self.post_payment()
        
        
    @api.onchange('student_id')
    def onchange_student(self):
        if self.student_id:
            self.admission_number = self.student_id.admission_number
            fee_domain = [('student_id', '=', self.student_id.id), ('state', '=', 'paid')]
            return {'domain': {'fee_collection_id': fee_domain}}
        else:
            return {'domain': {'fee_collection_id': [('student_id', '=', False)]}}

    @api.onchange('fee_collection_id')
    def onchange_fee_collection_id(self):
        if self.fee_collection_id:
            # self.student_id = self.fee_collection_id.student_id
            self.batch_id = self.fee_collection_id.batch_id
            self.admission_number = self.fee_collection_id.admission_number
            self.fee_type = self.fee_collection_id.fee_type
            self.refund_line = False
            new_lines = self.env['fee.refund.line']
            fees = self.env['fee.collection.line'].search(
                [('fee_collection_id', '=', self.fee_collection_id.id)])
            for fee in fees:
                data = {'fee_id': fee.fee_id,
                        'collected_amount': fee.amount,
                        'refund_amount': 0.0,
                        'month_id': fee.month_id.id,
                        'year': fee.year,
                        'academic_year': fee.academic_year,
                        'semester_id': fee.semester_id.id,
                        'due_id': fee.due_id.id
                        }
                new_line = new_lines.new(data)
                new_lines += new_line
            self.refund_line += new_lines

    @api.constrains('refund_line')
    def refund_amount_validation(self):
        for refund_fee in self.refund_line:
            if refund_fee.refund_amount > refund_fee.collected_amount:
                raise ValidationError(
                    _('Refund amount of %s is greater than paid amount') % (refund_fee.fee_id.name.upper()))


class RefundFeeLine(models.Model):
    _name = 'fee.refund.line'
    _description = 'Refund Fee Line'

    fee_id = fields.Many2one('fees.item')
    fee_refund_id = fields.Many2one('fee.refund')
    collected_amount = fields.Float()
    refund_amount = fields.Float()
    month_id = fields.Many2one('calendar.month')
    year = fields.Integer()
    semester_id = fields.Many2one('semester.semester')
    academic_year = fields.Integer()
    due_id = fields.Many2one('student.fee.dues')

    @api.model
    def create(self, values):
        # Add code here
        vals = {}
        if values['refund_amount'] > 0:
            vals = {
                'fee_id': values['fee_id'],
                'fee_refund_id': values['fee_refund_id'],
                'month_id': values['month_id'],
                'year': values['year'],
                'collected_amount': values['collected_amount'],
                'refund_amount': values['refund_amount'],
                'semester_id': values['semester_id'],
                'academic_year': values['academic_year'],
                'due_id': values['due_id'],
            }
        return super(RefundFeeLine, self).create(vals)


class AccountMove(models.Model):
    _inherit = 'account.move'

    fee_id = fields.Many2one('fee.collection')


class StudentFeeDues(models.Model):
    _name = 'student.fee.dues'
    _description = 'Student Fee Dues'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'

    student_id = fields.Many2one('student.student', track_visibility='onchange')
    admission_number = fields.Integer(related='student_id.admission_number', store=True)
    batch_id = fields.Many2one('batch.batch', related='student_id.batch_id', store=True)
    net_payable_amount = fields.Float(track_visibility='onchange')
    gross_payable_amount = fields.Float(track_visibility='onchange')
    paid_amount = fields.Float(track_visibility='onchange')
    discount_amount = fields.Float(track_visibility='onchange')
    scholarship_amount = fields.Float(track_visibility='onchange')
    balance = fields.Float(track_visibility='onchange')
    fee_id = fields.Many2one('fees.item', track_visibility='onchange')
    semester_id = fields.Many2one('semester.semester', track_visibility='onchange')
    installment_id = fields.Many2one('fee.installment')
    academic_year = fields.Integer(track_visibility='onchange')
    month_id = fields.Many2one('calendar.month')
    year = fields.Integer()
    date = fields.Date()
    refund = fields.Float()
    adjustment = fields.Float()

    @api.onchange('discount_amount', 'paid_amount', 'gross_payable_amount', 'scholarship_amount', 'refund', 'adjustment')
    def calculate_net_payable_amount(self):
        self.net_payable_amount = self.gross_payable_amount - self.discount_amount - self.scholarship_amount
        if self.paid_amount > self.net_payable_amount:
            raise UserError('%s should not be more than due (%s).' % (self.fee_id.name, self.balance))
        self.balance = self.net_payable_amount + self.refund - self.paid_amount 
        if self.balance < 0:
            raise UserError('Balance cannot be negative')
        if self.paid_amount < 0:
            raise UserError('Paid amount cannot be negative')
        if self.scholarship_amount < 0:
            raise UserError('Scholarship amount cannot be negative')
        if self.discount_amount < 0:
            raise UserError('Discount amount cannot be negative')
        if self.net_payable_amount < 0:
            raise UserError('Net Payable amount cannot be negative')


class FeePaymentSchedule(models.Model):
    _name = 'fee.payment.schedule'
    _description = 'Fee Payment Schedule'

    batch_ids = fields.Many2many('batch.batch')
    start_year = fields.Integer()
    semester_id = fields.Many2one('semester.semester')
    due_date = fields.Date('Due Date')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft')

    def confirm(self):
        fee_dues = self.env['student.fee.dues'].search(
            [('batch_id', 'in', self.batch_ids.ids), ('semester_id', '=', self.semester_id.id)])
        for fee_due in fee_dues:
            fee_due.write({
                'date': self.due_date
            })
        self.state = 'confirm'
