from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError


class MonthlyAdmissionWizard(models.TransientModel):
    _name = 'monthly.admission.count'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date to')
    programme_type = fields.Selection([('aided', 'Aided'), ('self_finance', 'Self Finance')], default='self_finance')

    def print_excel_report(self):
        domain = []
        if self.from_date:
            domain.append(('date_of_admission', '>=', self.from_date))
        if self.to_date:
            domain.append(('date_of_admission', '<=', self.to_date))
        record_ids = self.env['student.student'].sudo().search(domain)
        if len(record_ids) == 0:
            raise UserError("Records does not exist!!!")
        if not self.from_date and not self.to_date:
            raise UserError("Select date")
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'monthly.admission.count', 'form': self.read()[0]}
        return self.env.ref('safi_students.monthly_admission_count_xlsx_id').report_action(self, data=datas,
                                                                                           config=False)

    def generate_report(self):
        domain = []
        if self.from_date:
            domain.append(('date_of_admission', '>=', self.from_date))
        if self.to_date:
            domain.append(('date_of_admission', '<=', self.to_date))
        record_ids = self.env['student.student'].sudo().search(domain)
        if len(record_ids) == 0:
            raise UserError("Records does not exist!!!")
        if not self.from_date and not self.to_date:
            raise UserError("Select date")
        data = {'model_id': self.id, 'from_date': self.from_date, 'to_date': self.to_date,
                'programme_type': self.programme_type}
        return self.env.ref('safi_students.monthly_admission_count_pdf_id').report_action(self, data=data, config=False)


class MonthlyAdmissionCountPdf(models.Model):
    _name = 'report.safi_students.monthly_admission_count_pdf'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        lines = []
        if data['programme_type'] == 'aided':
            self_finance = False
        else:
            self_finance = True
        if data['from_date']:
            query = """ select count(ss.id),pp.level,trim(to_char(to_timestamp (date_part('month', ss.date_of_admission)::text, 'MM'), 'Month')) as month from student_student ss
                                inner join programme_programme pp on pp.id = ss.programme_id
                                WHERE ss.date_of_admission > '""" + str(data['from_date']) + """'
                                and ss.admission_number > 0 and pp.is_self_finance = """ + str(self_finance) + """
                                GROUP BY month,pp.level ORDER BY month DESC """
        if data['to_date']:
            query = """ select count(ss.id),pp.level,trim(to_char(to_timestamp (date_part('month', ss.date_of_admission)::text, 'MM'), 'Month')) as month from student_student ss
                                inner join programme_programme pp on pp.id = ss.programme_id
                                WHERE ss.date_of_admission < '""" + str(data['to_date']) + """'
                                and ss.admission_number > 0 and pp.is_self_finance = """ + str(self_finance) + """
                                GROUP BY month,pp.level ORDER BY month DESC """
        if data['from_date'] and data['to_date']:
            query = """ select count(ss.id),pp.level,trim(to_char(to_timestamp (date_part('month', ss.date_of_admission)::text, 'MM'), 'Month')) as month from student_student ss
                                inner join programme_programme pp on pp.id = ss.programme_id
                                WHERE ss.date_of_admission BETWEEN '""" + str(data['from_date']) + """' and  '""" + str(
                data['to_date']) + """'
                                and ss.admission_number > 0 and pp.is_self_finance = """ + str(self_finance) + """
                                GROUP BY month,pp.level ORDER BY month DESC """

        self.env.cr.execute(query)
        admission = self.env.cr.dictfetchall()
        lines = [{'month': month, 'ug': sum(
            [i['count'] for i in [item for item in admission] if i['month'] == month and i['level'] == 'ug']),
                  'pg': sum(
                      [i['count'] for i in [item for item in admission] if i['month'] == month and i['level'] == 'pg']),
                  'integrated': sum(
                      [i['count'] for i in [item for item in admission] if i['month'] == month and i['level'] == 'integrated'])
                  }
                 for month in list(dict.fromkeys(item['month'] for item in admission))]
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': lines,
        }


class MonthlyAdmissionCountXlsx(models.AbstractModel):
    _name = 'report.safi_students.monthly_admission_count_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})

        row = 3
        new_row = row + 1

        worksheet.merge_range(0, 0, 1, 14, 'Admission Statistics during'+str(invoices.from_date)+' to '+str(invoices.to_date), boldc)

        worksheet.merge_range(2, 0, 3, 0, 'Month', boldc)
        worksheet.merge_range(2, 1, 2, 4, 'UG', boldc)
        worksheet.merge_range(2, 5, 2, 7, 'PG', boldc)
        worksheet.merge_range(2, 8, 2, 13, 'Integrated', boldc)
        worksheet.merge_range(2, 14, 3, 14, 'Total', boldc)
        worksheet.write(3, 1, '1', boldc)
        worksheet.write(3, 2, '2', boldc)
        worksheet.write(3, 3, '3', boldc)
        worksheet.write(3, 4, 'Total', boldc)
        worksheet.write(3, 5, '1', boldc)
        worksheet.write(3, 6, '2', boldc)
        worksheet.write(3, 7, 'Total', boldc)
        worksheet.write(3, 8, '1', boldc)
        worksheet.write(3, 9, '2', boldc)
        worksheet.write(3, 10, '3', boldc)
        worksheet.write(3, 11, '4', boldc)
        worksheet.write(3, 12, '5', boldc)
        worksheet.write(3, 13, 'Total', boldc)

        domain = []
        if invoices.from_date:
            domain.append(('date_of_admission', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date_of_admission', '<=', invoices.to_date))
        new_row = 4
        if invoices.programme_type == 'aided':
            query = """ select count(ss.id),pp.level, s.name as semester,trim(to_char(to_timestamp (date_part('month', ss.date_of_admission)::text, 'MM'), 'Month')) as month from student_student ss
                        inner join programme_programme pp on pp.id = ss.programme_id
                        left join semester_semester s on s.id = ss.semester_id 
                        WHERE ss.date_of_admission BETWEEN '"""+str(invoices.from_date if invoices.from_date else '2000-01-01')+"""' and  '"""+str(invoices.to_date if invoices.to_date else '2050-01-01')+"""'
                        and ss.admission_number > 0 and pp.is_self_finance = false GROUP BY month,pp.level, s.name ORDER BY month DESC """
        else:
            query = """ select count(ss.id),pp.level, s.name as semester, trim(to_char(to_timestamp (date_part('month', ss.date_of_admission)::text, 'MM'), 'Month')) as month from student_student ss
                        inner join programme_programme pp on pp.id = ss.programme_id
                        left join semester_semester s on s.id = ss.semester_id 
                        WHERE ss.date_of_admission BETWEEN '"""+str(invoices.from_date if invoices.from_date else '2000-01-01')+"""' and  '"""+str(invoices.to_date if invoices.to_date else '2050-01-01')+"""'
                        and ss.admission_number > 0 and pp.is_self_finance = true GROUP BY month,pp.level, s.name ORDER BY month DESC """

        self.env.cr.execute(query)
        admission = self.env.cr.dictfetchall()
        # admission.keys()
        # students = self.env['student.student'].sudo().search(domain)
        month = admission[0]['month']
        tot_month = 0
        tot_ug = tot_pg = tot_integrated = tot_total = tot_ug_first = tot_ug_second = tot_ug_third = 0
        tot_pg_first = tot_pg_second = tot_integrated_first = tot_integrated_second = tot_integrated_third = tot_integrated_fourth = tot_integrated_fifth = 0
        ug_total = 0
        pg_total = 0
        integrated_total = 0
        for count in admission:
            if count['month'] != month:
                tot_total += tot_month
                tot_month = 0
                ug_total = 0
                pg_total = 0
                integrated_total = 0
                new_row+=1
            tot_month += count['count']
            worksheet.write(new_row, 0, count['month'], right)
            if count['level'] == 'ug':
                # ug_total = 0
                if count['semester'] in ['1', '2']:
                    ug_total += count['count']
                    tot_ug_first += count['count']
                    worksheet.write(new_row, 1, count['count'], right)
                if count['semester'] in ['3', '4']:
                    ug_total += count['count']
                    tot_ug_second += count['count']
                    worksheet.write(new_row, 2, count['count'], right)
                if count['semester'] in ['5', '6']:
                    ug_total += count['count']
                    tot_ug_third += count['count']
                    worksheet.write(new_row, 3, count['count'], right)
                worksheet.write(new_row, 4, ug_total, right)
                tot_ug += count['count']
            if count['level'] == 'pg':
                # pg_total = 0
                if count['semester'] in ['1', '2']:
                    pg_total += count['count']
                    tot_pg_first += count['count']
                    worksheet.write(new_row, 5, count['count'], right)
                if count['semester'] in ['3', '4']:
                    pg_total += count['count']
                    tot_pg_second += count['count']
                    worksheet.write(new_row, 6, count['count'], right)
                worksheet.write(new_row, 7, pg_total, right)
                tot_pg += count['count']
            if count['level'] == 'integrated':
                # integrated_total = 0
                if count['semester'] in ['1', '2']:
                    integrated_total += count['count']
                    tot_integrated_first += count['count']
                    worksheet.write(new_row, 8, count['count'], right)
                if count['semester'] in ['3', '4']:
                    integrated_total += count['count']
                    tot_integrated_second += count['count']
                    worksheet.write(new_row, 9, count['count'], right)
                if count['semester'] in ['5', '6']:
                    integrated_total += count['count']
                    tot_integrated_third += count['count']
                    worksheet.write(new_row, 10, count['count'], right)
                if count['semester'] in ['7', '8']:
                    integrated_total += count['count']
                    tot_integrated_fourth += count['count']
                    worksheet.write(new_row, 11, count['count'], right)
                if count['semester'] in ['9', '10']:
                    integrated_total += count['count']
                    tot_integrated_fifth += count['count']
                    worksheet.write(new_row, 12, count['count'], right)
                worksheet.write(new_row, 13, integrated_total, right)
                tot_integrated += count['count']
            worksheet.write(new_row, 14, tot_month, right)
            # tot_total += tot_month
            month = count['month']
        tot_total += tot_month
        worksheet.write(new_row+1, 0, 'Total', boldc)
        worksheet.write(new_row + 1, 1, tot_ug_first, boldr)
        worksheet.write(new_row + 1, 2, tot_ug_second, boldr)
        worksheet.write(new_row + 1, 3, tot_ug_third, boldr)
        worksheet.write(new_row + 1, 4, tot_ug, boldr)
        worksheet.write(new_row + 1, 5, tot_pg_first, boldr)
        worksheet.write(new_row + 1, 6, tot_pg_second, boldr)
        worksheet.write(new_row + 1, 7, tot_pg, boldr)
        worksheet.write(new_row + 1, 8, tot_integrated_first, boldr)
        worksheet.write(new_row + 1, 9, tot_integrated_second, boldr)
        worksheet.write(new_row + 1, 10, tot_integrated_third, boldr)
        worksheet.write(new_row + 1, 11, tot_integrated_fourth, boldr)
        worksheet.write(new_row + 1, 12, tot_integrated_fifth, boldr)
        worksheet.write(new_row + 1, 13, tot_integrated, boldr)
        worksheet.write(new_row + 1, 14, tot_total, boldr)
