from datetime import datetime
from odoo import api, fields, models
import collections


class StudentNominal(models.TransientModel):
    _name = 'nominal.roll'
    _description = 'Nominal Roll'

    year = fields.Selection(
        [(str(num), str(num)) for num in range(fields.Date.today().year - 8, fields.Date.today().year + 1)],
        default=datetime.now().year, string='Year')
    batch_ids = fields.Many2many('batch.batch', domain="[('start_year', '=', year)]")
    second_language_ids = fields.Many2many('second.language')

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'student.nominal', 'form': self.read()[0]}
        return self.env.ref('safi_students.nominal_roll_xlsx_id').report_action(self, data=datas, config=False)

    def generate_report(self):
        data = {'model_id': self.id, 'year': self.year, 'batch_ids': self.batch_ids.ids,
                'second_language_ids': self.second_language_ids.ids}
        return self.env.ref('safi_students.nominal_roll_pdf_id').report_action(self, data=data, config=False)


class StudentNominalRollPdf(models.Model):
    _name = 'report.safi_students.nominal_roll_pdf'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        lines = []
        domain = ['|', ('active', '=', True), ('active', '=', False)]
        domain1 = ['|', ('active', '=', True), ('active', '=', False)]
        repeat_domain = []
        domain.append(('admission_number', '>', 0))
        domain.append(('roll_no', '!=', False))
        domain1.append(('admission_number', '>', 0))
        domain1.append(('roll_no', '!=', False))
        repeat_domain.append(('admission_number', '>', 0))
        repeat_domain.append(('roll_no', '!=', False))
        if data['second_language_ids']:
            domain.append(('second_language_id', 'in', data['second_language_ids']))
            domain1.append(('second_language_id', 'in', data['second_language_ids']))
            repeat_domain.append(('second_language_id', 'in', data['second_language_ids']))
        for batch in self.env['batch.batch'].browse(data['batch_ids']):
            repeat_domain.append(('repeat_batch_id', '=', batch.id))
            repeat_domain.append(('semester_id', '=', batch.current_semester_id.id))
            domain.append(('batch_id', '=', batch.id))
            domain1.append(('batch_id', '=', batch.id))
            roll_no_list = self.env['student.student'].search(domain,
                                                              order='roll_order ASC, second_language_id ASC').mapped(
                'roll_no')
            roll_no_list += self.env['student.student'].search(repeat_domain,
                                                               order='roll_order ASC, second_language_id ASC').mapped(
                'roll_no')
            duplicate_roll_no_list = [item for item, count in collections.Counter(roll_no_list).items() if count > 1]
            old_students = self.env['student.student'].search(
                [('batch_id', '=', batch.id), ('roll_no', 'in', duplicate_roll_no_list), ('active', '=', False)]).ids
            domain1.append(('id', 'not in', old_students))
            student = self.env['student.student'].search(domain1, order='roll_order ASC, second_language_id ASC')
            lines.append({'batch': batch, 'students': student})
            domain = domain[:-1]
            domain1 = domain1[:-2]
            repeat_domain = repeat_domain[:-1]
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': lines,
        }


class NominalRollXlsx(models.AbstractModel):
    _name = 'report.safi_students.nominal_roll_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Nominal Roll")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})

        row = 2
        new_row = row + 1

        worksheet.merge_range(0, 0, 1, 5, self.env.company.name, boldc)
        domain = ['|', ('active', '=', True), ('active', '=', False)]
        domain1 = ['|', ('active', '=', True), ('active', '=', False)]
        repeat_domain = []
        # domain.append(('tcissued', '=', False))
        domain.append(('admission_number', '>', 0))
        domain.append(('roll_no', '!=', False))
        domain1.append(('admission_number', '>', 0))
        domain1.append(('roll_no', '!=', False))
        repeat_domain.append(('admission_number', '>', 0))
        repeat_domain.append(('roll_no', '!=', False))
        if invoices.second_language_ids:
            domain.append(('second_language_id', 'in', invoices.second_language_ids.ids))
            domain1.append(('second_language_id', 'in', invoices.second_language_ids.ids))
            repeat_domain.append(('second_language_id', 'in', invoices.second_language_ids.ids))
        for batch in self.env['batch.batch'].browse(invoices.batch_ids.ids):
            row += 1
            worksheet.merge_range(row, 0, row, 5, 'NOMINAL ROLL', boldc)
            worksheet.merge_range(row + 1, 0, row + 1, 5, batch.programme_id.name + ' (' + str(invoices.year) + ' Admission)', boldc)
            worksheet.write(row + 2, 0, 'SI.No', boldc)
            worksheet.write(row + 2, 1, 'Roll Number', boldc)
            worksheet.write(row + 2, 2, 'Admission Number', boldc)
            worksheet.write(row + 2, 3, 'Name', boldc)
            worksheet.write(row + 2, 4, 'Gender', boldc)
            worksheet.write(row + 2, 5, 'Language', boldc)
            repeat_domain.append(('repeat_batch_id', '=', batch.id))
            repeat_domain.append(('semester_id', '=', batch.current_semester_id.id))
            domain.append(('batch_id', '=', batch.id))
            domain1.append(('batch_id', '=', batch.id))
            roll_no_list = self.env['student.student'].search(domain, order='roll_order ASC, second_language_id ASC').mapped('roll_no')
            roll_no_list += self.env['student.student'].search(repeat_domain, order='roll_order ASC, second_language_id ASC').mapped('roll_no')
            duplicate_roll_no_list = [item for item, count in collections.Counter(roll_no_list).items() if count > 1]
            old_students = self.env['student.student'].search([('batch_id', '=', batch.id), ('roll_no', 'in', duplicate_roll_no_list), ('active', '=', False)]).ids
            domain1.append(('id', 'not in', old_students))
            students = self.env['student.student'].search(domain1, order='roll_order ASC, second_language_id ASC')
            i = 0
            new_row = row + 3
            for student in students:
                i += 1
                worksheet.write(new_row, 0, i, center)
                worksheet.write(new_row, 1, student.roll_no, left)
                if student.active:
                    worksheet.write(new_row, 2, student.admission_number, left)
                    worksheet.write(new_row, 3, student.name, left)
                    worksheet.write(new_row, 4, dict(student._fields['gender'].selection).get(student.gender), left)
                    worksheet.write(new_row, 5, student.second_language_id.name, left)
                new_row += 1
            domain = domain[:-1]
            domain1 = domain1[:-2]
            repeat_domain = repeat_domain[:-1]
            row = new_row + 1
