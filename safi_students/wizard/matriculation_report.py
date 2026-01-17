from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
import xlwt
import base64
import os


class MatriculationReportWizard(models.TransientModel):
    _name = 'matriculation.report.wizard'

    start_year = fields.Selection(
        [(str(num), str(num)) for num in range(datetime.now().year - 5, datetime.now().year + 1)])
    batch_id = fields.Many2one('batch.batch')

    def generate_report(self):
        data = {'model_id': self.id, 'start_year': self.start_year, 'batch_id': self.batch_id.id, }
        return self.env.ref('safi_students.matriculation_report_pdf_id').report_action(self, data=data, config=False)

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'matriculation.report.wizard', 'form': self.read()[0]}
        return self.env.ref('safi_students.matriculation_report_xlsx_id').report_action(self, data=datas, config=False)


class StudentMatriculationPdf(models.Model):
    _name = 'report.safi_students.matriculation_report_pdf'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        lines = []
        student_list = self.env['student.student'].search(
            [('batch_id', '=', data['batch_id']), ('admission_number', '!=', 0), ('tc_issued', '=', False)],
            order='roll_order')
        student_list = student_list + self.env['student.student'].search(
            [('batch_id', '=', data['batch_id']), ('admission_number', '!=', 0), ('tc_issued', '=', True)],
            order='roll_order')
        for student in student_list:
            if self.env['batch.batch'].browse([data['batch_id']]).programme_id.level in ['ug', 'integrated']:
                vals = {
                    'name': student.name,
                    'programme': student.batch_id.programme_id.name,
                    'reg_no': student.plus2_reg_no if student.plus2_reg_no else '',
                    'month': student.plus2_month if student.plus2_month else '',
                    'year': student.plus2_year if student.plus2_year else '',
                    'institute': student.plus2_school if student.plus2_school else '',
                    'board': student.plus2_board if student.plus2_board else '',
                    'admission_date': student.date_of_admission.strftime('%d-%m-%Y') if student.date_of_admission else ''
                }
                lines.append(vals)
            else:
                vals = {
                    'name': student.name,
                    'programme': student.batch_id.programme_id.name,
                    'reg_no': student.university_reg_no if student.university_reg_no else '',
                    'month': student.university_month if student.university_month else '',
                    'year': student.university_year if student.university_year else '',
                    'institute': student.college if student.college else '',
                    'board': student.university if student.university else '',
                    'admission_date': student.date_of_admission.strftime('%d-%m-%Y') if student.date_of_admission else ''
                }
                lines.append(vals)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': lines,
        }


class StudentMatriculationXlsx(models.AbstractModel):
    _name = 'report.safi_students.matriculation_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Matriculation")

        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})
        boldc.set_align('vcenter')
        y = 'Yes'
        n = 'No'
        worksheet.merge_range(0, 0, 1, 9, self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 3, 9, 'Consolidated list of candidates admitted to %s during %s-%s' % (
            invoices.batch_id.programme_id.name, invoices.start_year, str(int(invoices.start_year) + 1)), boldc)
        worksheet.merge_range(4, 0, 8, 0, 'SI No.', boldc)
        worksheet.merge_range(4, 1, 8, 1, 'Name of Candidate', boldc)
        worksheet.merge_range(4, 2, 8, 2, 'Programme \n to which \n admitted', boldc)
        worksheet.merge_range(4, 3, 8, 5,
                              'Name, Reg.No. & Year of \n passing the qualifying \n examination for admission to a \n '
                              'course/programme of study \n under this University',
                              boldc)
        worksheet.merge_range(4, 6, 8, 6,
                              'Name of College and University from \n which presented for qualifying examination & year'
                              , boldc)
        worksheet.merge_range(4, 7, 8, 7,
                              'Year in which and the \n college to which the \n candidate was first admitted \n '
                              'to a course of study under \n the university after passing S.S.L.C',
                              boldc)
        worksheet.merge_range(4, 8, 8, 8, 'Date on which \n migrated from this \n University and \n details of '
                                          'academic \n career pursued', boldc)
        worksheet.merge_range(4, 9, 8, 9, 'Date of \n admission', boldc)
        row = 9
        i = 0
        student_list = self.env['student.student'].search(
            ['|', ('active', '=', True), ('active', '=', False), ('batch_id', '=', invoices.batch_id.id),
             ('admission_number', '!=', 0), ('tc_issued', '=', False)], order='roll_order').mapped('id')
        student_list = student_list + self.env['student.student'].search(
            ['|', ('active', '=', True), ('active', '=', False), ('batch_id', '=', invoices.batch_id.id),
             ('admission_number', '!=', 0), ('tc_issued', '=', True)], order='roll_order').mapped('id')
        for student in self.env['student.student'].browse(student_list):
            if invoices.batch_id.programme_id.level in ['ug', 'integrated']:
                col = 0
                i += 1
                worksheet.write(row, col, i)
                if student.tc_issued:
                    worksheet.write(row, col + 1, student.name + ' (TC)')
                else:
                    worksheet.write(row, col + 1, student.name)
                worksheet.write(row, col + 2, student.programme_id.name if student.programme_id else '')
                worksheet.write(row, col + 3, student.plus2_reg_no if student.plus2_reg_no else '')
                worksheet.write(row, col + 4, student.plus2_month if student.plus2_month else '', center)
                worksheet.write(row, col + 5, student.plus2_year if student.plus2_year else '', center)
                worksheet.write(row, col + 6, student.plus2_school if student.plus2_school else '')
                worksheet.write(row, col + 7, student.plus2_board if student.plus2_board else '')
                worksheet.write(row, col + 8, '')
                worksheet.write(row, col + 9,
                                str(student.date_of_admission.strftime(
                                    '%d-%m-%Y') if student.date_of_admission else ''),
                                center)
                row += 1
            else:
                col = 0
                i += 1
                worksheet.write(row, col, i)
                if student.tc_issued:
                    worksheet.write(row, col + 1, student.name + ' (TC)')
                else:
                    worksheet.write(row, col + 1, student.name)
                worksheet.write(row, col + 2, student.programme_id.name if student.programme_id else '')
                worksheet.write(row, col + 3, student.university_reg_no if student.university_reg_no else '')
                worksheet.write(row, col + 4, student.university_month if student.university_month else '', center)
                worksheet.write(row, col + 5, student.university_year if student.university_year else '', center)
                worksheet.write(row, col + 6, student.college if student.college else '')
                worksheet.write(row, col + 7, student.university if student.university else '')
                worksheet.write(row, col + 8, '')
                worksheet.write(row, col + 9,
                                str(student.date_of_admission.strftime(
                                    '%d-%m-%Y') if student.date_of_admission else ''),
                                center)
                row += 1
