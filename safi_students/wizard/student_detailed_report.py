from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError


class AdmissionSummaryWizard(models.TransientModel):
    _name = 'student.detailed.report'

    @api.model
    def _get_default_start_year(self):
        return str(fields.Date.today().year)

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(num), str(num)) for num in range(current_year - 8, current_year + 1)]

    start_year = fields.Selection(
        _get_year_selection,
        default=_get_default_start_year, string='Batch Year')
    batch_ids = fields.Many2many('batch.batch')
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG'), ('integrated', 'Integrated')])
    report_type = fields.Selection(
        [('religion', 'Religion'), ('caste', 'Caste'), ('second_language', 'Second Language'),
         ('admission_category', 'Admission Category'), ('category', 'Caste Category'),
         ('fee_category', 'Fee Category')])
    field_select_ids = fields.Many2many('ir.model.fields')
    tc_status = fields.Selection([('Yes', 'Yes'), ('No', 'No'), ('Both', 'Both')], default='No', string='TC Status')
    religion_ids = fields.Many2many('religion.religion')
    caste_ids = fields.Many2many('caste.caste')
    caste_category_ids = fields.Many2many('caste.category')
    admission_category_ids = fields.Many2many('admission.category')
    fee_category_ids = fields.Many2many('fee.category')
    second_language_ids = fields.Many2many('second.language')

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'student.detailed.report', 'form': self.read()[0]}
        return self.env.ref('safi_students.student_detailed_report_xlsx_id').report_action(self, data=datas,
                                                                                                       config=False)


class StudentDetailedReportXlsx(models.AbstractModel):
    _name = 'report.safi_students.student_detailed_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        boldc_color = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        vertcal_align = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        boldr = workbook.add_format({'bold': True, 'align': 'right', 'border': 1})
        boldl = workbook.add_format({'bold': True, 'align': 'left', 'border': 1})
        bold = workbook.add_format({'bold': True, 'border': 1})
        center = workbook.add_format({'align': 'center', 'border': 1})
        right = workbook.add_format({'align': 'right', 'border': 1})
        left = workbook.add_format({'align': 'left', 'border': 1})
        vertcal_align.set_rotation(90)
        vertcal_align.set_align('vcenter')
        boldc.set_align('vcenter')
        center.set_align('vcenter')
        right.set_align('vcenter')
        boldl.set_align('vcenter')
        left.set_align('vcenter')
        boldc_color.set_bg_color('#DCDCDC')
        boldc_color.set_align('vcenter')

        row = 3
        new_row = row + 1
        if invoices.tc_status == 'Both':
            domain = ['|', ('active', '=', True), ('active', '=', False), ('admission_number', '>', 0)]
        else:
            domain = [('admission_number', '>', 0)]
        if invoices.tc_status == 'Yes':
            domain.append(('active', '=', False))
            domain.append(('tc_issued', '=', True))
        if invoices.religion_ids:
            domain.append(('religion', 'in', invoices.religion_ids.ids))
        if invoices.caste_ids:
            domain.append(('caste', 'in', invoices.caste_ids.ids))
        if invoices.caste_category_ids:
            domain.append(('caste_category_id', 'in', invoices.caste_category_ids.ids))
        if invoices.admission_category_ids:
            domain.append(('admission_category_id', 'in', invoices.admission_category_ids.ids))
        if invoices.fee_category_ids:
            domain.append(('fee_category_id', 'in', invoices.fee_category_ids.ids))
        if invoices.second_language_ids:
            domain.append(('second_language_id', 'in', invoices.second_language_ids.ids))
        col = 1
        query_list = []
        if invoices.report_type:
            length = len(invoices.field_select_ids) + 4
        else:
            length = len(invoices.field_select_ids) + 3
        if invoices.batch_ids:
            batches = invoices.batch_ids
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', invoices.start_year), ('programme_id.level', '=', invoices.level)])
        worksheet.merge_range(0, 0, 1, length,
                              self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, length, 'Student Details', boldc)
        students = self.env['student.student'].search(domain, order='name ASC')
        # worksheet.write(3, 0, 'SI', boldc)
        # worksheet.write(3, 1, 'Name', boldc)
        # worksheet.write(3, 2, 'Admission Number', boldc)
        # worksheet.write(3, 3, 'Roll Number', boldc)
        # if invoices.report_type == 'religion':
        #     worksheet.write(3, 4, 'Religion', boldc)
        # if invoices.report_type == 'caste':
        #     worksheet.write(3, 4, 'Caste', boldc)
        # if invoices.report_type == 'category':
        #     worksheet.write(3, 4, 'Caste Category', boldc)
        # if invoices.report_type == 'admission_category':
        #     worksheet.write(3, 4, 'Admission Category', boldc)
        # if invoices.report_type == 'fee_category':
        #     worksheet.write(3, 4, 'Fee Category', boldc)
        # if invoices.report_type == 'second_language':
        #     worksheet.write(3, 4, 'Second Language', boldc)
        # if invoices.field_select_ids:
        #     if invoices.report_type:
        #         col = 4
        #     else:
        #         col = 3
        #     for fields in invoices.field_select_ids:
        #         col += 1
        #         value = fields.field_description
        #         worksheet.write(row, col, value, boldc)
        row = 3
        for batch in batches:
            row += 1
            i = 0
            worksheet.set_row(row, 25)
            worksheet.merge_range(row, 0, row, length, batch.programme_id.name, boldc_color)
            row += 1
            worksheet.set_row(row, 25)
            worksheet.write(row, 0, 'SI', boldc)
            worksheet.write(row, 1, 'Name', boldc)
            worksheet.write(row, 2, 'Admission Number', boldc)
            worksheet.write(row, 3, 'Roll Number', boldc)
            if invoices.report_type == 'religion':
                worksheet.write(row, 4, 'Religion', boldc)
            if invoices.report_type == 'caste':
                worksheet.write(row, 4, 'Caste', boldc)
            if invoices.report_type == 'category':
                worksheet.write(row, 4, 'Caste Category', boldc)
            if invoices.report_type == 'admission_category':
                worksheet.write(row, 4, 'Admission Category', boldc)
            if invoices.report_type == 'fee_category':
                worksheet.write(row, 4, 'Fee Category', boldc)
            if invoices.report_type == 'second_language':
                worksheet.write(row, 4, 'Second Language', boldc)
            if invoices.field_select_ids:
                if invoices.report_type:
                    col = 4
                else:
                    col = 3
                for fields in invoices.field_select_ids:
                    col += 1
                    value = fields.field_description
                    worksheet.write(row, col, value, boldc)
            for student in students.filtered(lambda x: x.batch_id.id == batch.id):
                i += 1
                row += 1
                worksheet.write(row, 0, i, left)
                worksheet.write(row, 1, student.name, left)
                worksheet.write(row, 2, student.admission_number, left)
                worksheet.write(row, 3, student.roll_no, left)
                if invoices.report_type == 'religion':
                    worksheet.write(row, 4, student.religion.name, left)
                if invoices.report_type == 'caste':
                    worksheet.write(row, 4, student.caste.name, left)
                if invoices.report_type == 'category':
                    worksheet.write(row, 4, student.caste_category_id.name, left)
                if invoices.report_type == 'admission_category':
                    worksheet.write(row, 4, student.admission_category_id.name, left)
                if invoices.report_type == 'fee_category':
                    worksheet.write(row, 4, student.fee_category_id.name, left)
                if invoices.report_type == 'second_language':
                    worksheet.write(row, 4, student.second_language_id.name, left)
                if invoices.field_select_ids:
                    if invoices.report_type:
                        col = 4
                    else:
                        col = 3
                    for fields in invoices.field_select_ids:
                        col += 1
                        value = fields.name
                        if fields.ttype == 'many2one':
                            if fields.relation == 'batch.batch':
                                worksheet.write(row, col, student[value].complete_name if student[value] else '', left)
                            else:
                                worksheet.write(row, col, student[value].name if student[value] else '', left)
                        elif fields.ttype == 'date':
                            worksheet.write(row, col,
                                            str(student[value].strftime('%d/%m/%Y')) if student[value] else '', left)
                        elif fields.ttype == 'selection':
                            worksheet.write(row, col,
                                            dict(student._fields[value].selection).get(student[value]) if student[value] else '', left)
                            # dict(student._fields['gender'].selection).get(student.gender)
                        else:
                            worksheet.write(row, col, student[value] if student[value] else '', left)
