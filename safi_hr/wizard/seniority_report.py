from odoo import fields, models, api
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class SeniorityReportWizard(models.TransientModel):
    _name = 'seniority.report'
    _description = 'Seniority Report'

    staff_type = fields.Selection([('teaching', 'Teaching'), ('non_teaching', 'Non Teaching')])
    report_type = fields.Selection([('Department', 'Department'), ('General', 'General')])
    date = fields.Date()

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'seniority.report', 'form': self.read()[0]}
        return self.env.ref('safi_hr.seniority_report_xlsx_id').report_action(self, data=datas, config=False)


class SeniorityReportXlsx(models.AbstractModel):
    _name = 'report.safi_hr.seniority_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Bank Slip")

        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})
        boldc.set_align('vcenter')

        row = 3
        new_row = row + 1

        new_row = 4
        total_students = tot_student = []
        domain = []
        domain_1 = []
        r_no = 4
        c_no = 0
        worksheet.merge_range(0, 0, 0, 12, self.env.user.company_id.name, boldc)
        worksheet.merge_range(1, 0, 1, 12, 'DETAILS OF TEACHING STAFF AS ON %s' % invoices.date.strftime('%d/%m/%Y'), boldc)
        worksheet.merge_range(2, 0, 3, 0, 'SL.No', boldc)
        worksheet.merge_range(2, 1, 3, 1, 'Name', boldc)
        worksheet.merge_range(2, 2, 3, 2, 'Pen Number', boldc)
        worksheet.merge_range(2, 3, 3, 3, 'Gender', boldc)
        worksheet.merge_range(2, 4, 3, 4, 'Designation', boldc)
        worksheet.merge_range(2, 5, 3, 5, 'Department', boldc)
        worksheet.merge_range(2, 6, 3, 6, 'Date of birth', boldc)
        worksheet.merge_range(2, 7, 3, 7, 'Date of commencement of \n continous service', boldc)
        worksheet.merge_range(2, 8, 3, 8, 'Length of service', boldc)
        worksheet.merge_range(2, 9, 3, 9, 'Retirement Date', boldc)
        worksheet.merge_range(2, 10, 3, 10, 'Religion', boldc)
        worksheet.merge_range(2, 11, 3, 11, 'Caste', boldc)
        worksheet.merge_range(2, 12, 3, 12, 'Mobile Phone', boldc)
        i = 0
        # domain = ['|', ('active', '=', True), ('active', '=', False)]
        domain = []
        if invoices.staff_type:
            domain.append(('employee_type', '=', invoices.staff_type))
        if invoices.report_type == 'General':
            staff_list = self.env['hr.employee'].search(domain, order='date_of_joining ASC')
            # raise UserError(str(staff_list))
            i = 0
            for each in staff_list:
                i += 1
                date1 = each.date_of_joining
                date2 = invoices.date
                service = relativedelta(date2, date1).years
                worksheet.write(r_no, c_no, i, left)
                # worksheet.write(r_no, c_no + 1,
                #                 each.employee_title_id.name + ' ' + each.name if each.employee_title_id else '' + ' ' + each.name, left)
                worksheet.write(r_no, c_no + 1, each.name, left)
                worksheet.write(r_no, c_no + 2, each.pen_number if each.pen_number else '', left)
                worksheet.write(r_no, c_no + 3, dict(each._fields['gender'].selection).get(each.gender), left)
                worksheet.write(r_no, c_no + 4, each.job_id.name, left)
                worksheet.write(r_no, c_no + 5, each.department_id.name, left)
                worksheet.write(r_no, c_no + 6, str(each.birthday.strftime('%d/%m/%Y') if each.birthday else ''), left)
                worksheet.write(r_no, c_no + 7,
                                str(each.date_of_joining.strftime('%d/%m/%Y') if each.date_of_joining else ''), left)
                worksheet.write(r_no, c_no + 8, str(service) + ' Year', left)
                worksheet.write(r_no, c_no + 9, str(each.retirement_date.strftime('%d/%m/%Y') if each.retirement_date else ''), left)
                worksheet.write(r_no, c_no + 10, each.religion_id.name, left)
                worksheet.write(r_no, c_no + 11, each.caste_id.name, left)
                worksheet.write(r_no, c_no + 12, each.mobile_phone, left)
                r_no += 1
        else:
            principal = self.env['hr.employee'].search([('job_id.name', '=', 'Principal')])
            principal_date1 = principal.date_of_joining
            principal_date2 = invoices.date
            principal_service = relativedelta(principal_date2, principal_date1).years
            worksheet.merge_range(r_no, c_no, r_no, c_no + 11, 'Principal', boldc)
            worksheet.write(r_no + 1, c_no, 1, left)
            worksheet.write(r_no + 1, c_no + 1, principal.name, left)
            worksheet.write(r_no + 1, c_no + 2, principal.pen_number if principal.pen_number else '', left)
            worksheet.write(r_no + 1, c_no + 3, dict(principal._fields['gender'].selection).get(principal.gender), left)
            worksheet.write(r_no + 1, c_no + 4, principal.job_id.name, left)
            worksheet.write(r_no + 1, c_no + 5, principal.department_id.name, left)
            worksheet.write(r_no + 1, c_no + 6, str(principal.birthday.strftime('%d/%m/%Y') if principal.birthday else ''), left)
            worksheet.write(r_no + 1, c_no + 7,
                            str(principal.date_of_joining.strftime('%d/%m/%Y') if principal.date_of_joining else ''), left)
            worksheet.write(r_no + 1, c_no + 8, str(principal_service) + ' Year', left)
            worksheet.write(r_no + 1, c_no + 9, str(principal.retirement_date.strftime('%d/%m/%Y') if principal.retirement_date else ''), left)
            worksheet.write(r_no + 1, c_no + 10, principal.religion_id.name, left)
            worksheet.write(r_no + 1, c_no + 11, principal.caste_id.name, left)
            worksheet.write(r_no + 1, c_no + 12, principal.mobile_phone, left)
            r_no += 2
            domain.append(('id', '!=', principal.id))
            i = 1
            for department in self.env['hr.employee'].search(domain).mapped('department_id').sorted(
                    key=lambda r: r.sort_order):
                worksheet.merge_range(r_no, c_no, r_no, c_no + 11, department.name.upper(), boldc)
                domain.append(('department_id', '=', department.id))
                staff_list = self.env['hr.employee'].search(domain, order='date_of_joining ASC')
                for each in staff_list:
                    r_no += 1
                    i += 1
                    date1 = each.date_of_joining
                    date2 = invoices.date
                    service = relativedelta(date2, date1).years
                    worksheet.write(r_no, c_no, i, left)
                    worksheet.write(r_no, c_no + 1, each.name, left)
                    worksheet.write(r_no, c_no + 2, each.pen_number if each.pen_number else '', left)
                    worksheet.write(r_no, c_no + 3, dict(each._fields['gender'].selection).get(each.gender), left)
                    worksheet.write(r_no, c_no + 4, each.job_id.name, left)
                    worksheet.write(r_no, c_no + 5, each.department_id.name, left)
                    worksheet.write(r_no, c_no + 6, str(each.birthday.strftime('%d/%m/%Y') if each.birthday else ''), left)
                    worksheet.write(r_no, c_no + 7,
                                    str(each.date_of_joining.strftime('%d/%m/%Y') if each.date_of_joining else ''),
                                    left)
                    worksheet.write(r_no, c_no + 8, str(service) + ' Year', left)
                    worksheet.write(r_no, c_no + 9, str(each.retirement_date.strftime('%d/%m/%Y') if each.retirement_date else ''), left)
                    worksheet.write(r_no, c_no + 10, each.religion_id.name, left)
                    worksheet.write(r_no, c_no + 11, each.caste_id.name, left)
                    worksheet.write(r_no, c_no + 12, each.mobile_phone, left)
                domain.pop()
                r_no += 1
