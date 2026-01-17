from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
import xlsxwriter


class StudentFeeDues(models.TransientModel):
    _name = 'student.fee.due'

    batch_ids = fields.Many2many('batch.batch')
    # date = fields.Date()
    report_type = fields.Selection([('due_list', 'Due List'), ('collection_list', 'Collection List')],
                                   default='due_list')
    semester_id = fields.Many2one('semester.semester')
    to_date = fields.Date()

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'student.fee.due', 'form': self.read()[0]}
        return self.env.ref('safi_students.student_fee_due_xlsx_id').report_action(self, data=datas, config=False)


class StudentFeeDueXlsx(models.AbstractModel):
    _name = 'report.safi_students.student_fee_due_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Fee Due")

        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})
        worksheet.merge_range(0, 0, 1, 9, self.env.company.name, boldc)
        row = 4
        if invoices.report_type == 'due_list':
            worksheet.merge_range(2, 0, 2, 9, 'Due List of %s' % ','.join(invoices.batch_ids.mapped('complete_name')),
                                  boldc)
            worksheet.merge_range(3, 0, 3, 9,
                                  'Date : %s' % (invoices.to_date.strftime('%d/%m/%Y') if invoices.to_date else datetime.now().date().strftime('%d/%m/%Y')), boldc)
            worksheet.write(row, 0, 'SI', boldc)
            worksheet.write(row, 1, 'Name', boldc)
            worksheet.write(row, 2, 'Admission Number', boldc)
            worksheet.write(row, 3, 'Roll Number', boldc)
            worksheet.write(row, 4, 'Batch', boldc)
            worksheet.write(row, 5, 'Total Fee', boldc)
            worksheet.write(row, 6, 'Fee Paid', boldc)
            worksheet.write(row, 7, 'Balance', boldc)
            worksheet.write(row, 8, 'Mobile', boldc)
            worksheet.write(row, 9, 'Parent Mobile', boldc)
            row += 1
            students = self.env['student.student'].search([('batch_id', 'in', invoices.batch_ids.ids)],
                                                          order='batch_id, roll_order')
            i = 0
            for student in students:
                domain = [('student_id', '=', student.id)]
                fee_domain = [('student_id', '=', student.id), ('state', '=', 'paid')]
                if invoices.semester_id:
                    domain.append(('semester_id', '=', invoices.semester_id.id))
                    fee_domain.append(('semester_id', '=', invoices.semester_id.id))
                if invoices.to_date:
                    domain.append(('date', '<=', invoices.to_date))
                    fee_domain.append(('payment_date', '>', invoices.to_date))
                student_due = self.env['student.fee.dues'].search(domain)
                fee_collection = 0
                if invoices.to_date:
                    fee_collection = sum(self.env['fee.collection'].search(fee_domain).mapped('total'))
                balance = sum(student_due.mapped('balance')) + fee_collection
                if balance > 0 and student_due:
                    i += 1
                    net_payable_amount = sum(student_due.mapped('net_payable_amount'))
                    paid_amount = sum(student_due.mapped('paid_amount')) - fee_collection
                    # balance = sum(student_due.mapped('balance'))
                    worksheet.write(row, 0, i, center)
                    worksheet.write(row, 1, student.name, left)
                    worksheet.write(row, 2, student.admission_number, center)
                    worksheet.write(row, 3, student.roll_no, left)
                    worksheet.write(row, 4, student.batch_id.complete_name, left)
                    worksheet.write(row, 5, net_payable_amount, right)
                    worksheet.write(row, 6, paid_amount, right)
                    worksheet.write(row, 7, balance, right)
                    worksheet.write(row, 8, student.mobile, right)
                    worksheet.write(row, 9, student.parent_mobile, right)
                    row += 1
        else:
            worksheet.merge_range(2, 0, 2, 5, 'Collection List of %s' % ','.join(invoices.batch_ids.mapped('complete_name')), boldc)
            worksheet.merge_range(3, 0, 3, 5, 'Date : %s' % (invoices.to_date.strftime('%d/%m/%Y') if invoices.to_date else datetime.now().date().strftime('%d/%m/%Y')), boldc)
            worksheet.write(row, 0, 'SI', boldc)
            worksheet.write(row, 1, 'Name', boldc)
            worksheet.write(row, 2, 'Admission Number', boldc)
            worksheet.write(row, 3, 'Roll Number', boldc)
            worksheet.write(row, 4, 'Batch', boldc)
            worksheet.write(row, 5, 'Total Collected', boldc)
            row += 1
            students = self.env['student.student'].search(
                ['|', ('active', '=', True), ('active', '=', False), ('batch_id', 'in', invoices.batch_ids.ids)],
                order='batch_id, roll_order')
            i = 0
            for student in students:
                domain = [('student_id', '=', student.id), ('state', '=', 'paid')]
                if invoices.semester_id:
                    domain.append(('fee_line.semester_id', '=', invoices.semester_id.id))
                if invoices.to_date:
                    domain.append(('payment_date', '<=', invoices.to_date))
                fee_collection = self.env['fee.collection'].search(domain)
                i += 1
                paid_amount = sum(fee_collection.fee_line.filtered(lambda x: x.semester_id == invoices.semester_id).mapped('amount'))
                worksheet.write(row, 0, i, center)
                worksheet.write(row, 1, student.name + '(TC)' if student.active == False else student.name, left)
                worksheet.write(row, 2, student.admission_number, center)
                worksheet.write(row, 3, student.roll_no, left)
                worksheet.write(row, 4, student.batch_id.complete_name, left)
                worksheet.write(row, 5, paid_amount, right)
                row += 1
