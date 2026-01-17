from odoo import api, fields, models
import datetime
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError


class DetailedAdmissionSummaryXlsx(models.AbstractModel):
    _name = 'report.safi_students.detailed_admission_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
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
        row = 3
        new_row = row + 1
        domain = ['|', ('active', '=', False), ('active', '=', True), ('tc_issued', '=', False), ('admission_number', '>', 0)]
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        if invoices.religion_ids:
            domain.append(('religion_id', 'in', invoices.religion_ids.ids))
        if invoices.caste_ids:
            domain.append(('caste_id', 'in', invoices.caste_ids.ids))
        if invoices.caste_category_ids:
            domain.append(('caste_category_id', 'in', invoices.caste_category_ids.ids))
        if invoices.admission_category_ids:
            domain.append(('admission_category_id', 'in', invoices.admission_category_ids.ids))
        if invoices.fee_category_ids:
            domain.append(('fee_category_id', 'in', invoices.fee_category_ids.ids))
        if invoices.second_language_ids:
            domain.append(('second_language_id', 'in', invoices.second_language_ids.ids))
        col = 1
        if invoices.sort_order == 'religion':
            students = self.env['student.student'].search(domain, order='religion_id ASC, admission_number ASC')
        elif invoices.sort_order == 'caste':
            students = self.env['student.student'].search(domain, order='caste_id ASC, admission_number ASC')
        elif invoices.sort_order == 'second_language':
            students = self.env['student.student'].search(domain, order='second_language_id ASC, admission_number ASC')
        elif invoices.sort_order == 'admission_category':
            students = self.env['student.student'].search(domain, order='admission_category_id ASC, admission_number ASC')
        elif invoices.sort_order == 'category':
            students = self.env['student.student'].search(domain, order='caste_category_id ASC, admission_number ASC')
        elif invoices.sort_order == 'fee_category':
            students = self.env['student.student'].search(domain, order='fee_category_id ASC, admission_number ASC')
        elif invoices.sort_order == 'index':
            students = self.env['student.student'].search(domain, order='index DESC, admission_number ASC')
        else:
            students = self.env['student.student'].search(domain, order='admission_number ASC, admission_number ASC')
        query_list = []
        if invoices.detailed_report_type:
            length = len(invoices.field_select_ids) + 4
        else:
            length = len(invoices.field_select_ids) + 3
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
        else:
            if invoices.level:
                batches = students.mapped('batch_id').filtered(lambda x: x.programme_id.level == invoices.level)
            else:
                batches = students.mapped('batch_id')
        worksheet.merge_range(0, 0, 1, length, self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, length, 'Admission Details from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        row = 3
        for batch in batches:
            row += 1
            i = 0
            worksheet.merge_range(row, 0, row, length, batch.programme_id.name, boldc)
            worksheet.write(row + 1, 0, 'SI', boldc)
            worksheet.write(row + 1, 1, 'Name', boldc)
            worksheet.write(row + 1, 2, 'Admission Number', boldc)
            worksheet.write(row + 1, 3, 'Application Number', boldc)
            if invoices.detailed_report_type == 'religion':
                worksheet.write(row + 1, 4, 'Religion', boldc)
            if invoices.detailed_report_type == 'caste':
                worksheet.write(row + 1, 4, 'Caste', boldc)
            if invoices.detailed_report_type == 'category':
                worksheet.write(row + 1, 4, 'Caste Category', boldc)
            if invoices.detailed_report_type == 'admission_category':
                worksheet.write(row + 1, 4, 'Admission Category', boldc)
            if invoices.detailed_report_type == 'fee_category':
                worksheet.write(row + 1, 4, 'Fee Category', boldc)
            if invoices.detailed_report_type == 'second_language':
                worksheet.write(row + 1, 4, 'Second Language', boldc)
            if invoices.field_select_ids:
                if invoices.detailed_report_type:
                    col = 4
                else:
                    col = 3
                for fields in invoices.field_select_ids:
                    col += 1
                    value = fields.field_description
                    worksheet.write(row + 1, col, value, boldc)
            if invoices.fee_status == 'Yes':
                worksheet.write(row + 1, col + 1, 'Fee Status', boldc)
            row += 1
            for student in students.filtered(lambda x: x.batch_id.id == batch.id):
                i += 1
                row += 1
                worksheet.write(row, 0, i, left)
                worksheet.write(row, 1, student.name, left)
                worksheet.write(row, 2, student.admission_number, left)
                worksheet.write(row, 3, student.app_no, left)
                if invoices.detailed_report_type == 'religion':
                    worksheet.write(row, 4, student.religion_id.name, left)
                if invoices.detailed_report_type == 'caste':
                    worksheet.write(row, 4, student.caste_id.name, left)
                if invoices.detailed_report_type == 'category':
                    worksheet.write(row, 4, student.caste_category_id.name, left)
                if invoices.detailed_report_type == 'admission_category':
                    worksheet.write(row, 4, student.admission_category_id.name, left)
                if invoices.detailed_report_type == 'fee_category':
                    worksheet.write(row, 4, student.fee_category_id.name, left)
                if invoices.detailed_report_type == 'second_language':
                    worksheet.write(row, 4, student.second_language_id.name, left)
                if invoices.field_select_ids:
                    if invoices.detailed_report_type:
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
                        else:
                            worksheet.write(row, col, student[value] if student[value] else '', left)


class AdmissionSummaryReligionXlsx(models.AbstractModel):
    _name = 'report.safi_students.religion_admission_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Count Religion")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
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

        row = 4
        new_row = row + 1
        domain = ['|', ('active', '=', False), ('active', '=', True)]
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        col = 1
        query_list = []
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
            domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', int(invoices.batch_year)), ('programme_id.level', '=', invoices.level)])
            domain.append(('batch_id', 'in', batches.ids))
        religions = self.env['student.student'].search(domain).mapped('religion_id')
        length = len(religions)
        worksheet.merge_range(0, 0, 1, (length * 3 + 3), self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, (length * 3 + 3), 'Admission Statistics from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        for religion in religions:
            worksheet.merge_range(3, col, 3, col + 2, religion.name, boldc)
            worksheet.write(row, col, 'Male', boldc)
            worksheet.write(row, col + 1, 'Female', boldc)
            worksheet.write(row, col + 2, 'Total', boldc)
            col += 3
            query_list.append(""" SUM(CASE WHEN gender = 'male' AND religion_id = """ + str(religion.id) + """ THEN 1 
            ELSE 0 END) AS male_""" + str(religion.id) + """, SUM(CASE WHEN gender = 'female' AND religion_id = """ + str(
                religion.id) + """ THEN 1 
            ELSE 0 END) AS female_""" + str(religion.id) + """ , SUM(CASE WHEN religion_id = """ + str(religion.id) + """ 
            THEN 1 ELSE 0 END) AS total_""" + str(religion.id) + """ """)
        first_query = """ SELECT pp.name, pp.id,  """
        last_query = """, SUM(CASE WHEN gender = 'male' THEN 1 ELSE 0 END) AS total_male,
                     SUM(CASE WHEN gender = 'female' THEN 1 ELSE 0 END) AS total_female
                     FROM student_student ss INNER JOIN batch_batch bb ON bb.id = ss.batch_id INNER JOIN 
                     programme_programme pp ON pp.id = bb.programme_id WHERE ss.date_of_admission BETWEEN %s AND %s
                     AND ss.admission_number > 0 AND ss.tc_issued = false
                     GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        query = str(first_query) + str(','.join(query_list)) + str(last_query)
        aided_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == False).ids
        self_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == True).ids
        worksheet.merge_range(3, 0, row, 0, 'Programme', boldc)
        worksheet.merge_range(3, col, 3, col + 2, 'Grand Total', boldc)
        worksheet.write(row, col, 'Male', boldc)
        worksheet.write(row, col + 1, 'Female', boldc)
        worksheet.write(row, col + 2, 'Total', boldc)
        if aided_batch:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(aided_batch)])
            aided_batch_count = self.env.cr.dictfetchall()
            for each in aided_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                batch_tot = {}
                for religion in religions:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % religion.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % religion.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % religion.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)
        if self_batch:
            if aided_batch:
                row += 2
                worksheet.merge_range(row, 0, row, (length * 3 + 3), 'Self Finance', boldc)
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(self_batch)])
            self_batch_count = self.env.cr.dictfetchall()
            for each in self_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                for religion in religions:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % religion.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % religion.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % religion.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)


#                 Second Language

class AdmissionSummarySecondLanguageXlsx(models.AbstractModel):
    _name = 'report.safi_students.language_admission_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
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

        row = 4
        new_row = row + 1
        domain = ['|', ('active', '=', False), ('active', '=', True)]
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        col = 1
        query_list = []
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
            domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', int(invoices.batch_year)), ('programme_id.level', '=', invoices.level)])
            domain.append(('batch_id', 'in', batches.ids))
        languages = self.env['student.student'].search(domain).mapped('second_language_id')
        length = len(languages)
        worksheet.merge_range(0, 0, 1, (length * 3 + 3), self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, (length * 3 + 3), 'Admission Statistics from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        for language in languages:
            worksheet.merge_range(3, col, 3, col + 2, language.name, boldc)
            worksheet.write(row, col, 'Male', boldc)
            worksheet.write(row, col + 1, 'Female', boldc)
            worksheet.write(row, col + 2, 'Total', boldc)
            col += 3
            query_list.append(""" SUM(CASE WHEN gender = 'male' AND second_language_id = """ + str(language.id) + """ THEN 1 
            ELSE 0 END) AS male_""" + str(language.id) + """, SUM(CASE WHEN gender = 'female' AND second_language_id 
            = """ + str(language.id) + """ THEN 1 ELSE 0 END) AS female_""" + str(language.id) + """ 
            , SUM(CASE WHEN second_language_id = """ + str(language.id) + """ 
            THEN 1 ELSE 0 END) AS total_""" + str(language.id) + """ """)
        first_query = """ SELECT pp.name, pp.id,  """
        last_query = """, SUM(CASE WHEN gender = 'male' THEN 1 ELSE 0 END) AS total_male,
                     SUM(CASE WHEN gender = 'female' THEN 1 ELSE 0 END) AS total_female
                     FROM student_student ss INNER JOIN batch_batch bb ON bb.id = ss.batch_id INNER JOIN 
                     programme_programme pp ON pp.id = bb.programme_id WHERE ss.date_of_admission BETWEEN %s AND %s 
                     AND ss.admission_number > 0 AND ss.tc_issued = false
                     GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        query = str(first_query) + str(','.join(query_list)) + str(last_query)
        aided_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == False).ids
        self_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == True).ids
        worksheet.merge_range(3, 0, row, 0, 'Programme', boldc)
        worksheet.merge_range(3, col, 3, col + 2, 'Grand Total', boldc)
        worksheet.write(row, col, 'Male', boldc)
        worksheet.write(row, col + 1, 'Female', boldc)
        worksheet.write(row, col + 2, 'Total', boldc)
        if aided_batch:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(aided_batch)])
            aided_batch_count = self.env.cr.dictfetchall()
            for each in aided_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                batch_tot = {}
                for language in languages:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % language.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % language.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % language.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)
        if self_batch:
            if aided_batch:
                row += 2
                worksheet.merge_range(row, 0, row, (length * 3 + 3), 'Self Finance', boldc)
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(self_batch)])
            self_batch_count = self.env.cr.dictfetchall()
            for each in self_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                for language in languages:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % language.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % language.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % language.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)


#                 Caste

class AdmissionSummaryCasteXlsx(models.AbstractModel):
    _name = 'report.safi_students.caste_admission_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
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

        row = 4
        new_row = row + 1
        domain = ['|', ('active', '=', False), ('active', '=', True)]
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        col = 1
        query_list = []
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
            domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', int(invoices.batch_year)), ('programme_id.level', '=', invoices.level)])
            domain.append(('batch_id', 'in', batches.ids))
        castes = self.env['student.student'].search(domain).mapped('caste_id')
        length = len(castes)
        worksheet.merge_range(0, 0, 1, (length * 3 + 3), self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, (length * 3 + 3), 'Admission Statistics from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        for caste in castes:
            worksheet.merge_range(3, col, 3, col + 2, caste.name, boldc)
            worksheet.write(row, col, 'Male', boldc)
            worksheet.write(row, col + 1, 'Female', boldc)
            worksheet.write(row, col + 2, 'Total', boldc)
            col += 3
            query_list.append(""" SUM(CASE WHEN gender = 'male' AND caste_id = """ + str(caste.id) + """ THEN 1 
            ELSE 0 END) AS male_""" + str(caste.id) + """, SUM(CASE WHEN gender = 'female' AND caste_id 
            = """ + str(caste.id) + """ THEN 1 ELSE 0 END) AS female_""" + str(caste.id) + """ 
            , SUM(CASE WHEN caste_id = """ + str(caste.id) + """ THEN 1 ELSE 0 END) AS total_""" + str(caste.id) + """ """)
        first_query = """ SELECT pp.name, pp.id,  """
        last_query = """, SUM(CASE WHEN gender = 'male' THEN 1 ELSE 0 END) AS total_male,
                     SUM(CASE WHEN gender = 'female' THEN 1 ELSE 0 END) AS total_female
                     FROM student_student ss INNER JOIN batch_batch bb ON bb.id = ss.batch_id INNER JOIN 
                     programme_programme pp ON pp.id = bb.programme_id WHERE ss.date_of_admission BETWEEN %s AND %s 
                     AND ss.admission_number > 0 AND ss.tc_issued = false
                     GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        query = str(first_query) + str(','.join(query_list)) + str(last_query)
        aided_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == False).ids
        self_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == True).ids
        worksheet.merge_range(3, 0, row, 0, 'Programme', boldc)
        worksheet.merge_range(3, col, 3, col + 2, 'Grand Total', boldc)
        worksheet.write(row, col, 'Male', boldc)
        worksheet.write(row, col + 1, 'Female', boldc)
        worksheet.write(row, col + 2, 'Total', boldc)
        if aided_batch:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(aided_batch)])
            aided_batch_count = self.env.cr.dictfetchall()
            for each in aided_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                batch_tot = {}
                for caste in castes:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % caste.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % caste.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % caste.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)
        if self_batch:
            if aided_batch:
                row += 2
                worksheet.merge_range(row, 0, row, (length * 3 + 3), 'Self Finance', boldc)
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(self_batch)])
            self_batch_count = self.env.cr.dictfetchall()
            for each in self_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                for caste in castes:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % caste.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % caste.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % caste.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)


#                 Caste Category

class AdmissionSummaryCasteCategoryXlsx(models.AbstractModel):
    _name = 'report.safi_students.category_admission_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
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

        row = 4
        new_row = row + 1
        domain = ['|', ('active', '=', False), ('active', '=', True)]
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        col = 1
        query_list = []
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
            domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', int(invoices.batch_year)), ('programme_id.level', '=', invoices.level)])
            domain.append(('batch_id', 'in', batches.ids))
        caste_categories = self.env['student.student'].search(domain).mapped('caste_category_id')
        length = len(caste_categories)
        worksheet.merge_range(0, 0, 1, (length * 3 + 3), self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, (length * 3 + 3), 'Admission Statistics from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        for caste_category in caste_categories:
            worksheet.merge_range(3, col, 3, col + 2, caste_category.name, boldc)
            worksheet.write(row, col, 'Male', boldc)
            worksheet.write(row, col + 1, 'Female', boldc)
            worksheet.write(row, col + 2, 'Total', boldc)
            col += 3
            query_list.append(""" SUM(CASE WHEN gender = 'male' AND caste_category_id = """ + str(caste_category.id) + """ THEN 1 
            ELSE 0 END) AS male_""" + str(caste_category.id) + """, SUM(CASE WHEN gender = 'female' AND caste_category_id 
            = """ + str(caste_category.id) + """ THEN 1 ELSE 0 END) AS female_""" + str(caste_category.id) + """ 
            , SUM(CASE WHEN caste_category_id = """ + str(
                caste_category.id) + """ THEN 1 ELSE 0 END) AS total_""" + str(caste_category.id) + """ """)
        first_query = """ SELECT pp.name, pp.id,  """
        last_query = """, SUM(CASE WHEN gender = 'male' THEN 1 ELSE 0 END) AS total_male,
                     SUM(CASE WHEN gender = 'female' THEN 1 ELSE 0 END) AS total_female
                     FROM student_student ss INNER JOIN batch_batch bb ON bb.id = ss.batch_id INNER JOIN 
                     programme_programme pp ON pp.id = bb.programme_id WHERE ss.date_of_admission BETWEEN %s AND %s
                     AND ss.admission_number > 0 AND ss.tc_issued = false
                     GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        query = str(first_query) + str(','.join(query_list)) + str(last_query)
        aided_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == False).ids
        self_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == True).ids
        worksheet.merge_range(3, 0, row, 0, 'Programme', boldc)
        worksheet.merge_range(3, col, 3, col + 2, 'Grand Total', boldc)
        worksheet.write(row, col, 'Male', boldc)
        worksheet.write(row, col + 1, 'Female', boldc)
        worksheet.write(row, col + 2, 'Total', boldc)
        if aided_batch:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(aided_batch)])
            aided_batch_count = self.env.cr.dictfetchall()
            for each in aided_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                batch_tot = {}
                for caste_category in caste_categories:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % caste_category.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % caste_category.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % caste_category.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)
        if self_batch:
            if aided_batch:
                row += 2
                worksheet.merge_range(row, 0, row, (length * 3 + 3), 'Self Finance', boldc)
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(self_batch)])
            self_batch_count = self.env.cr.dictfetchall()
            for each in self_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                for caste_category in caste_categories:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % caste_category.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % caste_category.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % caste_category.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)


#                 Admission Category

class AdmissionSummaryAdmissionCategoryXlsx(models.AbstractModel):
    _name = 'report.safi_students.admission_category_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
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

        row = 4
        new_row = row + 1
        domain = ['|', ('active', '=', False), ('active', '=', True)]
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        col = 1
        query_list = []
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
            domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', int(invoices.batch_year)), ('programme_id.level', '=', invoices.level)])
            domain.append(('batch_id', 'in', batches.ids))
        admission_categories = self.env['student.student'].search(domain).mapped('admission_category_id')
        length = len(admission_categories)
        worksheet.merge_range(0, 0, 1, (length * 3 + 3), self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, (length * 3 + 3), 'Admission Statistics from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        for admission_category in admission_categories:
            worksheet.merge_range(3, col, 3, col + 2, admission_category.name, boldc)
            worksheet.write(row, col, 'Male', boldc)
            worksheet.write(row, col + 1, 'Female', boldc)
            worksheet.write(row, col + 2, 'Total', boldc)
            col += 3
            query_list.append(
                """ SUM(CASE WHEN gender = 'male' AND admission_category_id = """ + str(admission_category.id) + """ THEN 1 
            ELSE 0 END) AS male_""" + str(admission_category.id) + """, SUM(CASE WHEN gender = 'female' AND admission_category_id 
            = """ + str(admission_category.id) + """ THEN 1 ELSE 0 END) AS female_""" + str(admission_category.id) + """ 
            , SUM(CASE WHEN admission_category_id = """ + str(
                    admission_category.id) + """ THEN 1 ELSE 0 END) AS total_""" + str(admission_category.id) + """ """)
        first_query = """ SELECT pp.name, pp.id,  """
        last_query = """, SUM(CASE WHEN gender = 'male' THEN 1 ELSE 0 END) AS total_male,
                     SUM(CASE WHEN gender = 'female' THEN 1 ELSE 0 END) AS total_female
                     FROM student_student ss INNER JOIN batch_batch bb ON bb.id = ss.batch_id INNER JOIN 
                     programme_programme pp ON pp.id = bb.programme_id WHERE ss.date_of_admission BETWEEN %s AND %s 
                     AND ss.admission_number > 0 AND ss.tc_issued = false
                     GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        query = str(first_query) + str(','.join(query_list)) + str(last_query)
        aided_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == False).ids
        self_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == True).ids
        worksheet.merge_range(3, 0, row, 0, 'Programme', boldc)
        worksheet.merge_range(3, col, 3, col + 2, 'Grand Total', boldc)
        worksheet.write(row, col, 'Male', boldc)
        worksheet.write(row, col + 1, 'Female', boldc)
        worksheet.write(row, col + 2, 'Total', boldc)
        if aided_batch:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(aided_batch)])
            aided_batch_count = self.env.cr.dictfetchall()
            for each in aided_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                batch_tot = {}
                for admission_category in admission_categories:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % admission_category.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % admission_category.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % admission_category.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)
        if self_batch:
            if aided_batch:
                row += 2
                worksheet.merge_range(row, 0, row, (length * 3 + 3), 'Self Finance', boldc)
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(self_batch)])
            self_batch_count = self.env.cr.dictfetchall()
            for each in self_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                for admission_category in admission_categories:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % admission_category.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % admission_category.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % admission_category.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)


#                 Fee Category

class AdmissionSummaryFeeCategoryXlsx(models.AbstractModel):
    _name = 'report.safi_students.fee_admission_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
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

        row = 4
        new_row = row + 1
        domain = ['|', ('active', '=', False), ('active', '=', True)]
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        col = 1
        query_list = []
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
            domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', int(invoices.batch_year)), ('programme_id.level', '=', invoices.level)])
            domain.append(('batch_id', 'in', batches.ids))
        fee_categories = self.env['student.student'].search(domain).mapped('fee_category_id')
        length = len(fee_categories)
        worksheet.merge_range(0, 0, 1, (length * 3 + 3), self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, (length * 3 + 3), 'Admission Statistics from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        for fee_category in fee_categories:
            worksheet.merge_range(3, col, 3, col + 2, fee_category.name, boldc)
            worksheet.write(row, col, 'Male', boldc)
            worksheet.write(row, col + 1, 'Female', boldc)
            worksheet.write(row, col + 2, 'Total', boldc)
            col += 3
            query_list.append(""" SUM(CASE WHEN gender = 'male' AND fee_category_id = """ + str(fee_category.id) + """ THEN 1 
            ELSE 0 END) AS male_""" + str(fee_category.id) + """, SUM(CASE WHEN gender = 'female' AND fee_category_id 
            = """ + str(fee_category.id) + """ THEN 1 ELSE 0 END) AS female_""" + str(fee_category.id) + """ 
            , SUM(CASE WHEN fee_category_id = """ + str(fee_category.id) + """ THEN 1 ELSE 0 END) AS total_""" + str(
                fee_category.id) + """ """)
        first_query = """ SELECT pp.name, pp.id,  """
        last_query = """, SUM(CASE WHEN gender = 'male' THEN 1 ELSE 0 END) AS total_male,
                     SUM(CASE WHEN gender = 'female' THEN 1 ELSE 0 END) AS total_female
                     FROM student_student ss INNER JOIN batch_batch bb ON bb.id = ss.batch_id INNER JOIN 
                     programme_programme pp ON pp.id = bb.programme_id WHERE ss.date_of_admission BETWEEN %s AND %s 
                     AND ss.admission_number > 0 AND ss.tc_issued = false
                     GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        query = str(first_query) + str(','.join(query_list)) + str(last_query)
        aided_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == False).ids
        self_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == True).ids
        worksheet.merge_range(3, 0, row, 0, 'Programme', boldc)
        worksheet.merge_range(3, col, 3, col + 2, 'Grand Total', boldc)
        worksheet.write(row, col, 'Male', boldc)
        worksheet.write(row, col + 1, 'Female', boldc)
        worksheet.write(row, col + 2, 'Total', boldc)
        if aided_batch:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(aided_batch)])
            aided_batch_count = self.env.cr.dictfetchall()
            for each in aided_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                batch_tot = {}
                for fee_category in fee_categories:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % fee_category.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % fee_category.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % fee_category.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)
        if self_batch:
            if aided_batch:
                row += 2
                worksheet.merge_range(row, 0, row, (length * 3 + 3), 'Self Finance', boldc)
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(self_batch)])
            self_batch_count = self.env.cr.dictfetchall()
            for each in self_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                for fee_category in fee_categories:
                    col += 1
                    worksheet.write(row, col, each['male_%d' % fee_category.id], right)
                    worksheet.write(row, col + 1, each['female_%d' % fee_category.id], right)
                    worksheet.write(row, col + 2, each['total_%d' % fee_category.id], right)
                    col += 2
                col += 1
                worksheet.write(row, col, each['total_male'], right)
                worksheet.write(row, col + 1, each['total_female'], right)
                worksheet.write(row, col + 2, each['total_male'] + each['total_female'], right)
