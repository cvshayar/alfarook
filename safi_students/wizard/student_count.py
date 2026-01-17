from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
import datetime
import collections


class StudentCountWizard(models.TransientModel):
    _name = 'student.count.report'

    to_date = fields.Date(default=fields.Date.today())
    batch_year = fields.Selection(
        [(str(num), str(num)) for num in range(fields.Date.today().year - 8, fields.Date.today().year + 1)],
        default=fields.Date.today().year, string='Batch Year')
    programme_ids = fields.Many2many('programme.programme', domain="[('level','=','ug')]")
    report_type = fields.Selection(
        [('religion', 'Religion'), ('caste', 'Caste'), ('second_language', 'Second Language'),
         ('admission_category', 'Admission Category'), ('category', 'Caste Category')])
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG')])

    def print_excel_report(self):
        domain = [('date_of_admission', '<=', self.to_date),
                  ('batch_id.start_year', '=', self.batch_year)]
        if self.level:
            domain.append(('programme_id.level', '=', self.level))
        if self.programme_ids:
            domain.append(('programme_id', 'in', self.programme_ids.ids))
            programme = self.env['programme.programme'].search([('id', 'in', self.programme_ids.ids)])
        else:
            programme = self.env['programme.programme'].search([('level', '=', self.level)])
        students = self.env['student.student'].search(domain)
        # raise UserError((tuple(programme.ids)))
        if self.report_type == 'second_language':
            # category_list = self.env['second.language'].search([])
            category_list = students.mapped('second_language_id').sorted(key=lambda x: x.name)
        if self.report_type == 'religion':
            # category_list = self.env['religion.religion'].search([])
            category_list = students.mapped('religion_id').sorted(key=lambda x: x.name)
        if self.report_type == 'caste':
            # category_list = self.env['caste.caste'].search([])
            category_list = students.mapped('caste_id').sorted(key=lambda x: x.name)
        if self.report_type == 'admission_category':
            # category_list = self.env['admission.category'].search([])
            category_list = students.mapped('admission_category_id').sorted(key=lambda x: x.name)
        if self.report_type == 'category':
            # category_list = self.env['caste.category'].search([], order='sort_order')
            category_list = students.mapped('caste_category_id').sorted(key=lambda x: x.sort_order)
        if not category_list:
            raise UserError(str('No Data'))
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'student.count.report',
                 'form': self.read()[0]}
        return self.env.ref('safi_students.student_count_report_xlsx_id').report_action(self, data=datas, config=False)


class StudentCountReportXlsx(models.AbstractModel):
    _name = 'report.safi_students.student_count_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Count")

        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})

        row = 3
        new_row = row + 1

        new_row = 4
        total_students = tot_student = []
        programme_domain = []
        r_no = c_no = 2
        student_count = []
        worksheet.merge_range(0, 0, 0, 15, self.env.company.name, boldc)
        if invoices.report_type == 'religion':
            worksheet.merge_range(1, 0, 1, 15, 'Religion wise student count report till %s' % str(
                invoices.to_date.strftime('%d/%m/%Y')), boldc)
        if invoices.report_type == 'caste':
            worksheet.merge_range(1, 0, 1, 15, 'Caste wise student count report till %s' % str(
                invoices.to_date.strftime('%d/%m/%Y')), boldc)
        if invoices.report_type == 'second_language':
            worksheet.merge_range(1, 0, 1, 15, 'Second language wise student count report till %s' % str(
                invoices.to_date.strftime('%d/%m/%Y')), boldc)
        if invoices.report_type == 'admission_category':
            worksheet.merge_range(1, 0, 1, 15, 'Admission category wise student count report till %s' % str(
                invoices.to_date.strftime('%d/%m/%Y')), boldc)
        if invoices.report_type == 'category':
            worksheet.merge_range(1, 0, 1, 15, 'Caste category wise student count report till %s' % str(
                invoices.to_date.strftime('%d/%m/%Y')), boldc)
        domain = [('date_of_admission', '<=', invoices.to_date),
                  ('batch_id.start_year', '=', invoices.batch_year)]
        if invoices.level:
            domain.append(('programme_id.level', '=', invoices.level))
        if invoices.programme_ids:
            domain.append(('programme_id', 'in', invoices.programme_ids.ids))
            programme = self.env['programme.programme'].search([('id', 'in', invoices.programme_ids.ids)])
        else:
            if invoices.level:
                programme = self.env['programme.programme'].search([('level', '=', invoices.level)])
            else:
                programme = self.env['programme.programme'].search([])
        students = self.env['student.student'].search(domain)
        # raise UserError((tuple(programme.ids)))
        if invoices.report_type == 'second_language':
            # category_list = self.env['second.language'].search([])
            category_list = students.mapped('second_language_id').sorted(key=lambda x: x.name)
        if invoices.report_type == 'religion':
            # category_list = self.env['religion.religion'].search([])
            category_list = students.mapped('religion_id').sorted(key=lambda x: x.name)
        if invoices.report_type == 'caste':
            # category_list = self.env['caste.caste'].search([])
            category_list = students.mapped('caste_id').sorted(key=lambda x: x.name)
        if invoices.report_type == 'admission_category':
            # category_list = self.env['admission.category'].search([])
            category_list = students.mapped('admission_category_id').sorted(key=lambda x: x.name)
        if invoices.report_type == 'category':
            # category_list = self.env['caste.category'].search([], order='sort_order')
            category_list = students.mapped('caste_category_id').sorted(key=lambda x: x.sort_order)
        # query = """ SELECT REGEXP_REPLACE(pp.name, ^\s+$', '') """
        worksheet.merge_range(2, 0, 2, 1, '', boldc)
        list = []
        for each in category_list:
            'tot' + str(each.id)
            # if invoices.report_type == 'second_language':
            if each.name == 'OBC Muslim':
                worksheet.merge_range(r_no, c_no, r_no, c_no + 2, 'OBC', boldc)
            elif each.name == 'OBC':
                worksheet.merge_range(r_no, c_no, r_no, c_no + 2, 'OBC Other than muslim', boldc)
            else:
                worksheet.merge_range(r_no, c_no, r_no, c_no + 2, each.name, boldc)
            worksheet.merge_range(r_no + 1, 0, r_no + 1, 1, 'Programme', boldc)
            worksheet.write(r_no + 1, c_no, 'Male', boldc)
            worksheet.write(r_no + 1, c_no + 1, 'Female', boldc)
            worksheet.write(r_no + 1, c_no + 2, 'Total', boldc)
            if invoices.report_type == 'second_language':
                list.append(""" sum(case when gender = 'male' and second_language_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'male' + str(each.id) + """,
                sum(case when gender = 'female' and second_language_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'female' + str(each.id) + """,
                sum(case when gender in ('female','male') and second_language_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'total' + str(each.id) + """ """)
            if invoices.report_type == 'religion':
                list.append(""" sum(case when gender = 'male' and religion_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'male' + str(each.id) + """,
                sum(case when gender = 'female' and religion_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'female' + str(each.id) + """,
                sum(case when gender in ('female','male') and religion_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """ 'total' + str(each.id) + """ """)
            if invoices.report_type == 'caste':
                list.append(""" sum(case when gender = 'male' and caste_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'male' + str(each.id) + """,
                sum(case when gender = 'female' and caste_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'female' + str(each.id) + """,
                sum(case when gender in ('female','male') and caste_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """'total' + str(each.id) + """ """)
            if invoices.report_type == 'admission_category':
                list.append(""" sum(case when gender = 'male' and admission_category_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """ 'male' + str(each.id) + """,
                sum(case when gender = 'female' and admission_category_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """ 'female' + str(each.id) + """,
                sum(case when gender in ('female','male') and admission_category_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """ 'total' + str(each.id) + """ """)
            if invoices.report_type == 'category':
                list.append(""" sum(case when gender = 'male' and caste_category_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """ 'male' + str(each.id) + """,
                sum(case when gender = 'female' and caste_category_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """ 'female' + str(each.id) + """,
                sum(case when gender in ('female','male') and caste_category_id= """ + str(
                    each.id) + """ then 1 else 0 end) as """ 'total' + str(each.id) + """ """)
            c_no += 3
        worksheet.merge_range(r_no, c_no, r_no, c_no + 2, ' Grand Total', boldc)
        worksheet.write(r_no + 1, c_no, 'Total Male', boldc)
        worksheet.write(r_no + 1, c_no + 1, 'Total Female', boldc)
        worksheet.write(r_no + 1, c_no + 2, 'Total', boldc)
        list = ','.join(list)
        query = """ SELECT pp.name as programme,pp.id ,  """
        last_query_aided = """, sum(case when gender = 'male' then 1 else 0 end) as """'total_male' + str(
            each.id) + """, sum(case when gender = 'female' then 1 else 0 end) as """'total_female' + str(
            each.id) + """
        ,count(*) as """'total_count' + str(each.id) + """  from student_student ss INNER JOIN programme_programme pp on pp.id = ss.programme_id INNER JOIN batch_batch bb on bb.id = ss.batch_id 
        LEFT JOIN caste_caste cc ON cc.id = ss.caste_id LEFT JOIN caste_category ca on ca.id = cc.category
        LEFT JOIN tc_issued_register tc ON tc.admission_number=ss.admission_number  
        LEFT JOIN student_non_promotion snp ON snp.admission_number=ss.admission_number 
        WHERE bb.start_year= """ + str(
            invoices.batch_year) + """ AND ss.admission_number!=0  AND pp.level='""" + str(
            invoices.level) + """'  AND (tc.tc_issued_date IS NULL OR tc.tc_issued_date>'""" + str(
            invoices.to_date if invoices.to_date else datetime.now().date()) + """')  AND pp.is_self_finance = False
            AND ss.date_of_admission <= '""" + str(invoices.to_date) + """'
            AND (snp.date IS NULL OR snp.date > '""" + str(invoices.to_date) + """')
        group by pp.name, pp.id HAVING pp.id in %s order by pp.sort_order"""

        last_query_self_finance = """, sum(case when gender = 'male' then 1 else 0 end) as """'total_male' + str(
            each.id) + """, sum(case when gender = 'female' then 1 else 0 end) as """'total_female' + str(
            each.id) + """
                ,count(*) as """'total_count' + str(each.id) + """  from student_student ss INNER JOIN programme_programme pp on pp.id = ss.programme_id INNER JOIN batch_batch bb on bb.id = ss.batch_id 
                LEFT JOIN caste_caste cc ON cc.id = ss.caste_id LEFT JOIN caste_category ca on ca.id = cc.category
                LEFT JOIN tc_issued_register tc ON tc.admission_number=ss.admission_number 
                LEFT JOIN student_non_promotion snp ON snp.admission_number=ss.admission_number  
                WHERE bb.start_year= """ + str(
            invoices.batch_year) + """ AND ss.admission_number!=0
            AND (tc.tc_issued_date IS NULL OR tc.tc_issued_date>'""" + str(
            invoices.to_date if invoices.to_date else datetime.now().date()) + """')  AND pp.is_self_finance = True
            AND ss.date_of_admission <= '""" + str(invoices.to_date) + """'
            AND (snp.date IS NULL OR snp.date > '""" + str(invoices.to_date) + """')
                group by pp.name, pp.id HAVING pp.id in %s order by pp.sort_order"""
        # raise UserError(str(list))
        final_query_aided = str(query) + str(list) + str(last_query_aided)
        final_query_self_finance = str(query) + str(list) + str(last_query_self_finance)
        if programme.filtered(lambda x: x.is_self_finance == False).ids:
            self.env.cr.execute(final_query_aided,
                                [tuple(programme.filtered(lambda x: x.is_self_finance == False).ids)])
            student_count_aided = self.env.cr.dictfetchall()
        if programme.filtered(lambda x: x.is_self_finance == True).ids:
            self.env.cr.execute(final_query_self_finance,
                                [tuple(programme.filtered(lambda x: x.is_self_finance == True).ids)])
            student_count_self_finance = self.env.cr.dictfetchall()

        # for student in ini_dict:
        #     for k in d.keys():
        #         result[k] = result.get(k, 0) + d[k]
        batch_r_no = r_no + 2
        result_aided = {}
        counter = collections.Counter()
        counter_aided = collections.Counter()
        if programme.filtered(lambda x: x.is_self_finance == False).ids:
            for count in student_count_aided:
                counter.update(count if count else 0)
                counter_aided.update(count if count else 0)
                result_aided = dict(counter_aided)
                c_no = 2
                worksheet.merge_range(batch_r_no, 0, batch_r_no, 1, count['programme'], left)
                tot_male = tot_female = tot_total = 0
                for language in category_list:
                    # worksheet.write(batch_r_no, c_no, count['malayalam_male'], left)
                    worksheet.write(batch_r_no, c_no,
                                    count['male' + str(language.id)] if count['male' + str(language.id)] > 0 else '',
                                    right)
                    worksheet.write(batch_r_no, c_no + 1, count['female' + str(language.id)] if count['female' + str(
                        language.id)] > 0 else '', right)
                    worksheet.write(batch_r_no, c_no + 2,
                                    count['total' + str(language.id)] if count['total' + str(language.id)] > 0 else '',
                                    right)
                    if count['male' + str(language.id)]:
                        tot_male += int(count['male' + str(language.id)])
                    if count['female' + str(language.id)]:
                        tot_female += int(count['female' + str(language.id)])
                    if count['total' + str(language.id)]:
                        tot_total += int(count['total' + str(language.id)])
                    c_no += 3
                # if (int(count[str(language.name).lower() + '_total_male']) - tot_total) > 0:
                # Undefined Category
                # worksheet.merge_range(r_no, c_no, r_no, c_no + 2, ' Not defined', boldc)
                # worksheet.write(r_no + 1, c_no, 'Total Male', boldc)
                # worksheet.write(r_no + 1, c_no + 1, 'Total Female', boldc)
                # worksheet.write(r_no + 1, c_no + 2, 'Total', boldc)
                # worksheet.write(batch_r_no, c_no, int(count['total_male'+str(language.id)]) - tot_male, left)
                # worksheet.write(batch_r_no, c_no + 1, int(count['total_female'+str(language.id)]) - tot_female, left)
                # worksheet.write(batch_r_no, c_no + 2, int(count['total_count'+str(language.id)]) - tot_total, left)

                # Total Programme wise
                worksheet.write(batch_r_no, c_no, count['total_male' + str(language.id)] if count['total_male' + str(
                    language.id)] > 0 else '', right)
                worksheet.write(batch_r_no, c_no + 1, count['total_female' + str(language.id)] if count[
                                                                                                      'total_female' + str(
                                                                                                          language.id)] > 0 else '',
                                right)
                worksheet.write(batch_r_no, c_no + 2, count['total_count' + str(language.id)] if count[
                                                                                                     'total_count' + str(
                                                                                                         language.id)] > 0 else '',
                                right)
                batch_r_no += 1
            # raise UserError(str(result))
            c_no = 2
            removed_value = result_aided.pop('programme')
            removed_value = result_aided.pop('id')
            # raise UserError(str(result))
            worksheet.merge_range(batch_r_no, 0, batch_r_no, 1, 'Total', boldc)
            for total_count in result_aided.values():
                worksheet.write(batch_r_no, c_no, total_count if total_count > 0 else '', boldc)
                c_no += 1

        #     Self finance student count
        result = {}
        if programme.filtered(lambda x: x.is_self_finance == True).ids:
            batch_r_no = batch_r_no + 3
            worksheet.merge_range(batch_r_no - 1, 0, batch_r_no - 1, 15, 'Self finance', boldc)
            result_self_finance = {}
            counter_self_finance = collections.Counter()
            for count in student_count_self_finance:
                counter_self_finance.update(count if count else 0)
                counter.update(count if count else 0)
                result = dict(counter)
                result_self_finance = dict(counter_self_finance)
                c_no = 2
                worksheet.merge_range(batch_r_no, 0, batch_r_no, 1, count['programme'], left)
                tot_male = tot_female = tot_total = 0
                for language in category_list:
                    # worksheet.write(batch_r_no, c_no, count['malayalam_male'], left)
                    worksheet.write(batch_r_no, c_no,
                                    count['male' + str(language.id)] if count['male' + str(language.id)] > 0 else '',
                                    right)
                    worksheet.write(batch_r_no, c_no + 1, count['female' + str(language.id)] if count['female' + str(
                        language.id)] > 0 else '', right)
                    worksheet.write(batch_r_no, c_no + 2,
                                    count['total' + str(language.id)] if count['total' + str(language.id)] > 0 else '',
                                    right)
                    if count['male' + str(language.id)]:
                        tot_male += int(count['male' + str(language.id)])
                    if count['female' + str(language.id)]:
                        tot_female += int(count['female' + str(language.id)])
                    if count['total' + str(language.id)]:
                        tot_total += int(count['total' + str(language.id)])
                    c_no += 3
                # if (int(count[str(language.name).lower() + '_total_male']) - tot_total) > 0:
                # Undefined Category
                # worksheet.merge_range(r_no, c_no, r_no, c_no + 2, ' Not defined', boldc)
                # worksheet.write(r_no + 1, c_no, 'Total Male', boldc)
                # worksheet.write(r_no + 1, c_no + 1, 'Total Female', boldc)
                # worksheet.write(r_no + 1, c_no + 2, 'Total', boldc)
                # worksheet.write(batch_r_no, c_no, int(count['total_male'+str(language.id)]) - tot_male, left)
                # worksheet.write(batch_r_no, c_no + 1, int(count['total_female'+str(language.id)]) - tot_female, left)
                # worksheet.write(batch_r_no, c_no + 2, int(count['total_count'+str(language.id)]) - tot_total, left)

                # Total Programme wise
                worksheet.write(batch_r_no, c_no, count['total_male' + str(language.id)] if count['total_male' + str(
                    language.id)] > 0 else '', right)
                worksheet.write(batch_r_no, c_no + 1, count['total_female' + str(language.id)] if count[
                                                                                                      'total_female' + str(
                                                                                                          language.id)] > 0 else '',
                                right)
                worksheet.write(batch_r_no, c_no + 2, count['total_count' + str(language.id)] if count[
                                                                                                     'total_count' + str(
                                                                                                         language.id)] > 0 else '',
                                right)
                batch_r_no += 1
                # raise UserError(str(result))
            c_no = 2
            removed_value = result_self_finance.pop('programme')
            removed_value = result_self_finance.pop('id')
            # raise UserError(str(result))
            worksheet.merge_range(batch_r_no, 0, batch_r_no, 1, 'Total', boldc)
            for total_count in result_self_finance.values():
                worksheet.write(batch_r_no, c_no, total_count if total_count > 0 else '', boldc)
                c_no += 1
        if programme.filtered(lambda x: x.is_self_finance == False).ids and programme.filtered(
                lambda x: x.is_self_finance == True).ids:
            c_no = 2
            worksheet.merge_range(batch_r_no + 2, 0, batch_r_no + 2, 1, 'Grand Total', boldc)
            removed_value = result.pop('programme')
            removed_value = result.pop('id')
            for total_count in result.values():
                worksheet.write(batch_r_no + 2, c_no, total_count if total_count > 0 else '', boldc)
                c_no += 1
