from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from odoo.osv import expression


class StudentTransfer(models.Model):
    _name = 'student.transfer'
    _description = 'Student Transfer'

    name = fields.Integer('Sequence')
    admission_number = fields.Integer()
    transferred_date = fields.Date('transferred Date', default=fields.Date.today)
    student_id = fields.Many2one('student.student')
    new_student_id = fields.Many2one('student.student')
    # student = fields.Selection(_get_students, string='Old Students')
    from_batch_id = fields.Many2one('batch.batch')
    to_batch_id = fields.Many2one('batch.batch', string='transferred to')
    remarks = fields.Text()
    state = fields.Selection([('draft', 'Draft'), ('transferred', 'Transferred')], string='state', default='draft')

    @api.onchange('student_id')
    def onchange_student(self):
        if self.student_id:
            self.admission_number = self.student_id.admission_number
            self.from_batch_id = self.student_id.batch_id

    def transfer_student(self):
        transfer = self.env['student.transfer'].search([('state', '=', 'transferred')], order='name DESC', limit=1)
        self.name = transfer.name + 1 if transfer else 1
        student = self.env['student.student'].search([('admission_number', '=', self.admission_number)])
        if self.to_batch_id.programme_id.is_self_finance == self.from_batch_id.programme_id.is_self_finance:
            student.write(
                {'batch_id': self.to_batch_id.id, 'programme_id': self.to_batch_id.programme_id.id})
        if self.to_batch_id.current_semester_id.name in ['1', '2']:
            academic_year = self.to_batch_id.start_year
        elif self.to_batch_id.current_semester_id.name in ['3', '4']:
            academic_year = self.to_batch_id.start_year + 1
        else:
            academic_year = self.to_batch_id.start_year + 2
        programme_fees = self.env['programme.fee'].search(
            [('programme_ids', 'in', self.to_batch_id.programme_id.ids), ('academic_year', '=', academic_year),
             ('fee_category_ids', 'in', self.student_id.fee_category_id.ids),
             ('semester_id', '=', self.student_id.semester_id.id), ('state', '=', 'confirmed')])
        fee_dues = self.env['student.fee.dues'].search(
            [('student_id', '=', self.student_id.id), ('semester_id', '=', self.student_id.semester_id.id)])
        for each in fee_dues:
            programme_fee = programme_fees.programme_line.filtered(lambda x: x.fee_id.id == each.fee_id.id)
            each.write({'gross_payable_amount': programme_fee.amount})
            each.calculate_net_payable_amount()
        self.state = 'transferred'
