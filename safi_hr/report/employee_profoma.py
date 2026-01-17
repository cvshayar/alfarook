from dateutil.relativedelta import relativedelta
from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date


class EmployeeProformaReportXlsx(models.AbstractModel):
    _name = 'report.safi_hr.employee_proforma_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Employee Proforma")

        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})
        boldc.set_align('vcenter')
        center.set_align('vcenter')

        row = 3
        new_row = row + 1

        new_row = 4
        total_students = tot_student = []
        domain = []
        domain_1 = []
        worksheet.merge_range(0, 0, 0, 12, self.env.user.company_id.name, boldc)
        # worksheet.merge_range(1, 0, 1, 12, 'DETAILS OF TEACHING STAFF AS ON %s' % invoices.date.strftime('%d/%m/%Y'), boldc)
        worksheet.merge_range(2, 0, 7, 0, 'SL.No', boldc)
        worksheet.merge_range(2, 1, 7, 1, 'Name of \n Incumbent', boldc)
        worksheet.merge_range(2, 2, 7, 2, 'Pen Number', boldc)
        worksheet.merge_range(2, 3, 7, 3, 'Department', boldc)
        worksheet.merge_range(2, 4, 7, 4, 'Designation', boldc)
        worksheet.merge_range(2, 5, 5, 10, 'Qualification (with date & class)', boldc)
        worksheet.merge_range(6, 5, 7, 5, '               PG              ', center)
        worksheet.merge_range(6, 6, 7, 6, 'NET', center)
        worksheet.merge_range(6, 7, 7, 7, 'PhD', center)
        worksheet.merge_range(6, 8, 7, 8, 'MPhil', center)
        worksheet.merge_range(6, 9, 7, 9, 'Additional \n PG', center)
        worksheet.merge_range(6, 10, 7, 10, 'Other', center)
        worksheet.merge_range(2, 11, 7, 11, 'Details of \n Probation', boldc)
        worksheet.merge_range(2, 12, 7, 12, 'Details of \n service in \n other \n department', boldc)
        worksheet.merge_range(2, 13, 7, 13, 'Sex', boldc)
        worksheet.merge_range(2, 14, 7, 14, 'Length of \n Service', boldc)
        worksheet.merge_range(2, 15, 7, 15, 'Religion', boldc)
        worksheet.merge_range(2, 16, 7, 16, 'Caste', boldc)
        worksheet.merge_range(2, 17, 7, 17, 'Permanent \n Address', boldc)
        worksheet.merge_range(2, 18, 7, 18, 'Voting \n Constituency', boldc)
        worksheet.merge_range(2, 19, 7, 19, 'Official \n Address', boldc)
        worksheet.merge_range(2, 20, 5, 22, 'Phone \n Number', boldc)
        worksheet.merge_range(6, 20, 7, 20, 'Mobile', center)
        worksheet.merge_range(6, 21, 7, 21, 'Whatsapp', center)
        worksheet.merge_range(6, 22, 7, 22, 'Residence', center)
        worksheet.merge_range(2, 23, 7, 23, 'E-mail \n ID', boldc)
        worksheet.merge_range(2, 24, 7, 24, 'Aadhar \n No', boldc)
        worksheet.merge_range(2, 25, 7, 25, 'PAN Card \n No', boldc)
        worksheet.merge_range(2, 26, 7, 26, 'DoB', boldc)
        worksheet.merge_range(2, 27, 7, 27, 'DoJ', boldc)
        worksheet.merge_range(2, 28, 7, 28, 'Details of \n Break up \n Service', boldc)
        worksheet.merge_range(2, 29, 5, 30, 'Approval order \n Details', boldc)
        worksheet.merge_range(6, 29, 7, 29, '           No            ', center)
        worksheet.merge_range(6, 30, 7, 30, 'Date', center)
        worksheet.merge_range(2, 31, 7, 31, 'Conditional \n Approval \n Details', boldc)
        worksheet.merge_range(2, 32, 7, 32, 'Details of \n Refresher \n Course', boldc)
        worksheet.merge_range(2, 33, 7, 33, 'Details of \n Orientation \n Course', boldc)
        worksheet.merge_range(2, 34, 5, 37, 'Salary Details', boldc)
        worksheet.merge_range(6, 34, 7, 34, 'Scale', center)
        worksheet.merge_range(6, 35, 7, 35, 'Basic', center)
        worksheet.merge_range(6, 36, 7, 36, 'AGP', center)
        worksheet.merge_range(6, 37, 7, 37, 'Stage', center)
        worksheet.merge_range(2, 38, 7, 38, 'Details of \n Presentation', boldc)
        worksheet.merge_range(2, 39, 7, 39, 'Details of \n Publication', boldc)
        worksheet.merge_range(2, 40, 7, 40, 'Details of \n Advisorship', boldc)
        worksheet.merge_range(2, 41, 7, 41, 'Details of \n other \n committees', boldc)
        worksheet.merge_range(2, 42, 7, 42, 'Movement of \n Service Book', boldc)
        i = 0
        domain = ['|', ('active', '=', True), ('active', '=', False), ('retirement_date', '>', invoices.date)]
        # domain = []
        if invoices.staff_type:
            domain.append(('employee_type', '=', invoices.staff_type))
        staff_list = self.env['hr.employee'].search(domain, order='date_of_joining ASC')
        r_no = 8
        c_no = 0
        for each in staff_list:
            i += 1
            # basic = self.env['bill.entry'].search(
            #     [('pen_number', '=', each.pen_number), ('bill_item_id.name', '=', 'B Pay/L.Sal')], order='id DESC',
            #     limit=1).amount
            # agp = self.env['bill.entry'].search(
            #     [('pen_number', '=', each.pen_number), ('bill_item_id.name', '=', 'AGP')], order='id DESC',
            #     limit=1).amount
            basic = agp = 0
            # presentations = len(self.env['employee.publications'].search(
            #     [('presentation_type', '=', 'presentation'), ('employee_id', '=', each.id)]))
            # publications = len(self.env['employee.publications'].search(
            #     [('presentation_type', '=', 'publication'), ('employee_id', '=', each.id)]))
            presentations = publications = 0
            refresher_course = len(self.env['employee.inservice'].search(
                [('employee_id', '=', each.id), ('inservice_course_id.name', '=', 'Refresher Course')]))
            orientation_course = len(self.env['employee.inservice'].search(
                [('employee_id', '=', each.id), ('inservice_course_id.name', '=', 'Orientation Course')]))
            adivisership = len(self.env['employee.advisership'].search([('employee_id', '=', each.id)]))
            committee = len(self.env['employee.committee'].search([('employee_id', '=', each.id)]))
            # service_book = len(self.env['employee.service.book'].search([('employee_id', '=', each.id)]))
            service_book = 0
            date1 = each.date_of_joining
            date2 = invoices.date
            service = relativedelta(date2, date1).years
            worksheet.write(r_no, c_no, i, left)
            worksheet.write(r_no, c_no + 1, each.name, left)
            worksheet.write(r_no, c_no + 2, each.pen_number if each.pen_number else '', left)
            worksheet.write(r_no, c_no + 3, each.department_id.name, left)
            worksheet.write(r_no, c_no + 4, each.job_id.name, left)
            worksheet.write(r_no, c_no + 13, each.gender, left)
            worksheet.write(r_no, c_no + 14, str(service) + ' Years', left)
            worksheet.write(r_no, c_no + 15, each.religion_id.name if each.religion_id else '', left)
            worksheet.write(r_no, c_no + 16, each.caste_id.name if each.caste_id else '', left)
            worksheet.write(r_no, c_no + 17, each.address if each.address else '', left)
            worksheet.write(r_no, c_no + 18, each.constituency_id.name if each.constituency_id else '', left)
            worksheet.write(r_no, c_no + 20, each.mobile_phone if each.mobile_phone else '', left)
            worksheet.write(r_no, c_no + 21, each.mobile_phone if each.mobile_phone else '', left)
            worksheet.write(r_no, c_no + 22, each.work_phone if each.work_phone else '', left)
            worksheet.write(r_no, c_no + 23, each.work_email if each.work_email else '', left)
            worksheet.write(r_no, c_no + 24, each.aadhar_number if each.aadhar_number else '', left)
            worksheet.write(r_no, c_no + 25, each.pan_number if each.pan_number else '', left)
            worksheet.write(r_no, c_no + 26, str(each.birthday.strftime('%d/%m/%Y')) if each.birthday else '', left)
            worksheet.write(r_no, c_no + 27,
                            str(each.date_of_joining.strftime('%d/%m/%Y')) if each.date_of_joining else '', left)
            worksheet.write(r_no, c_no + 29, each.approval_order if each.approval_order else '', left)
            worksheet.write(r_no, c_no + 30,
                            str(each.approval_order_date.strftime('%d/%m/%Y')) if each.approval_order_date else '',
                            left)
            worksheet.write(r_no, c_no + 32, refresher_course if refresher_course > 0 else '', left)
            worksheet.write(r_no, c_no + 33, orientation_course if orientation_course > 0 else '', left)
            worksheet.write(r_no, c_no + 34, '', left)
            worksheet.write(r_no, c_no + 35, basic if basic > 0 else '', left)
            worksheet.write(r_no, c_no + 36, agp if agp > 0 else '', left)
            worksheet.write(r_no, c_no + 38, presentations if presentations > 0 else '', left)
            worksheet.write(r_no, c_no + 39, publications if publications > 0 else '', left)
            worksheet.write(r_no, c_no + 40, adivisership if adivisership > 0 else '', left)
            worksheet.write(r_no, c_no + 41, committee if committee > 0 else '', left)
            worksheet.write(r_no, c_no + 42, service_book if service_book > 0 else '', left)
            r_no += 1


class EmployeeQualificationReportXlsx(models.AbstractModel):
    _name = 'report.safi_hr.employee_qualification_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Employee Proforma")

        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        boldr = workbook.add_format({'bold': True, 'align': 'right'})
        boldl = workbook.add_format({'bold': True, 'align': 'left'})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        right = workbook.add_format({'align': 'right'})
        left = workbook.add_format({'align': 'left'})
        boldc.set_align('vcenter')
        center.set_align('vcenter')

        row = 3
        new_row = row + 1

        new_row = 4
        total_students = tot_student = []
        domain = []
        domain_1 = []
        worksheet.merge_range(0, 0, 0, 12, self.env.user.company_id.name, boldc)
        # worksheet.merge_range(1, 0, 1, 12, 'DETAILS OF TEACHING STAFF AS ON %s' % invoices.date.strftime('%d/%m/%Y'), boldc)
        worksheet.merge_range(2, 0, 7, 0, 'SL.No', boldc)
        worksheet.merge_range(2, 1, 7, 1, 'Name of \n Incumbent', boldc)
        worksheet.merge_range(2, 2, 7, 2, 'Pen Number', boldc)
        worksheet.merge_range(2, 3, 7, 3, 'Department', boldc)
        worksheet.merge_range(2, 4, 7, 4, 'Designation', boldc)
        worksheet.merge_range(2, 5, 5, 10, 'Qualification (with date & class)', boldc)
        worksheet.merge_range(6, 5, 7, 5, '               PG              ', center)
        worksheet.merge_range(6, 6, 7, 6, 'NET', center)
        worksheet.merge_range(6, 7, 7, 7, 'PhD', center)
        worksheet.merge_range(6, 8, 7, 8, 'MPhil', center)
        worksheet.merge_range(6, 9, 7, 9, 'Additional \n PG', center)
        worksheet.merge_range(6, 10, 7, 10, 'Other', center)
        worksheet.merge_range(2, 11, 7, 11, 'Details of \n Probation', boldc)
        worksheet.merge_range(2, 12, 7, 12, 'Sex', boldc)
        worksheet.merge_range(2, 13, 7, 13, 'Length of \n Service', boldc)
        worksheet.merge_range(2, 14, 7, 14, 'Religion', boldc)
        worksheet.merge_range(2, 15, 7, 15, 'Caste', boldc)
        worksheet.merge_range(2, 16, 7, 16, 'Permanent \n Address', boldc)
        worksheet.merge_range(2, 17, 7, 17, 'Voting \n Constituency', boldc)
        worksheet.merge_range(2, 18, 7, 18, 'Official \n Address', boldc)
        worksheet.merge_range(2, 19, 5, 21, 'Phone \n Number', boldc)
        worksheet.merge_range(6, 19, 7, 19, 'Mobile', center)
        worksheet.merge_range(6, 20, 7, 20, 'Whatsapp', center)
        worksheet.merge_range(6, 21, 7, 21, 'Residence', center)
        worksheet.merge_range(2, 22, 7, 22, 'E-mail \n ID', boldc)
        worksheet.merge_range(2, 23, 7, 23, 'Aadhar \n No', boldc)
        worksheet.merge_range(2, 24, 7, 24, 'PAN Card \n No', boldc)
        worksheet.merge_range(2, 25, 7, 25, 'DoB', boldc)
        worksheet.merge_range(2, 26, 7, 26, 'DoJ', boldc)
        worksheet.merge_range(2, 27, 5, 28, 'Approval order \n Details', boldc)
        worksheet.merge_range(6, 27, 7, 27, '           No            ', center)
        worksheet.merge_range(6, 28, 7, 28, 'Date', center)
        worksheet.merge_range(2, 29, 5, 33, 'Salary Details', boldc)
        worksheet.merge_range(6, 29, 7, 29, 'Scale', center)
        worksheet.merge_range(6, 30, 7, 30, 'Basic', center)
        worksheet.merge_range(6, 31, 7, 31, 'AGP', center)
        worksheet.merge_range(6, 32, 7, 32, 'Stage', center)
        worksheet.merge_range(6, 33, 7, 33, 'HRA', center)
        worksheet.merge_range(2, 34, 7, 34, 'Movement of \n Service Book', boldc)
        i = 0
        domain = ['|', ('active', '=', True), ('active', '=', False), ('retirement_date', '>', invoices.date)]
        # domain = []
        domain1 = []
        if invoices.staff_type:
            domain.append(('employee_type', '=', invoices.staff_type))
        if invoices.from_date:
            domain1.append(('date', '>=', invoices.from_date))
        if invoices.to_date:
            domain1.append(('date', '<=', invoices.to_date))
        staff_list = self.env['hr.employee'].search(domain, order='join_sequence ASC')  # Getting as on date staff list
        domain1.append(('employee_id', 'in', staff_list.ids))
        if not invoices.qualification_ids:
            qualifications = self.env['qualification.level'].search([])
        else:
            qualifications = self.env['qualification.level'].browse(invoices.qualification_ids.ids)
        r_no = 8
        c_no = 0
        for qualification in qualifications:
            worksheet.merge_range(r_no, 0, r_no, 15, qualification.name, boldc)
            r_no += 1
            domain1.append(('level_id', '=', qualification.id))
            staff_list = self.env['hr.qualification'].search(domain1).mapped('employee_id').sorted(key='join_sequence')
            # staff_list = staff_list.mapped('employee_qualification_ids').filtered(lambda x: x.level_id.id == qualification.id).mapped('employee_id').sorted(key='join_sequence')
            for each in staff_list:
                i += 1
                # basic = self.env['bill.entry'].search(
                #     [('pen_number', '=', each.pen_number), ('bill_item_id.name', '=', 'B Pay/L.Sal')], order='id DESC',
                #     limit=1).amount
                # agp = self.env['bill.entry'].search(
                #     [('pen_number', '=', each.pen_number), ('bill_item_id.name', '=', 'AGP')], order='id DESC',
                #     limit=1).amount
                # hra = self.env['bill.entry'].search(
                #     [('pen_number', '=', each.pen_number), ('bill_item_id.name', '=', 'HRA')], order='id DESC',
                #     limit=1).amount
                basic = agp = hra = 0
                service_book = self.env['employee.service.book'].sudo().search([('employee_id', '=', each.id)],
                                                                        order='date DESC', limit=1)
                pgs = each.employee_qualification_ids.filtered(lambda x: x.level_id.name == 'PG')
                nets = each.employee_qualification_ids.filtered(lambda x: x.level_id.name == 'NET')
                phds = each.employee_qualification_ids.filtered(lambda x: x.level_id.name == 'PhD')
                mphils = each.employee_qualification_ids.filtered(lambda x: x.level_id.name == 'MPhil')
                add_pgs = each.employee_qualification_ids.filtered(lambda x: x.level_id.name == 'Additional PG')
                others = each.employee_qualification_ids.filtered(
                    lambda x: x.level_id.name not in ['PG', 'NET', 'PhD', 'MPhil', 'Additional PG'])
                pg_list = []
                net_list = []
                phd_list = []
                mphil_list = []
                add_pg_list = []
                other_list = []

                for pg in pgs:
                    pg_list.append(str(pg.date.strftime('%d/%m/%Y') if pg.date else '') + '  ' + str(
                        pg.grade if pg.grade else ''))
                for net in nets:
                    net_list.append(str(net.date.strftime('%d/%m/%Y') if net.date else '') + '  ' + str(
                        net.grade if net.grade else ''))
                for phd in phds:
                    phd_list.append(str(phd.date.strftime('%d/%m/%Y') if phd.date else '') + '  ' + str(
                        phd.grade if phd.grade else ''))
                for mphil in mphils:
                    mphil_list.append(str(mphil.date.strftime('%d/%m/%Y') if mphil.date else '') + '  ' + str(
                        mphil.grade if mphil.grade else ''))
                for add_pg in add_pgs:
                    add_pg_list.append(str(add_pg.date.strftime('%d/%m/%Y') if add_pg.date else '') + '  ' + str(
                        add_pg.grade if add_pg.grade else ''))
                for other in others:
                    other_list.append(str(other.level_id.name) + ' ' + str(other.date.strftime('%d/%m/%Y') if other.date else '') + '  ' + str(
                        other.grade if other.grade else ''))
                date1 = each.date_of_joining
                date2 = invoices.date
                service = relativedelta(date2, date1).years
                worksheet.write(r_no, c_no, i, left)
                worksheet.write(r_no, c_no + 1, each.name, left)
                worksheet.write(r_no, c_no + 2, each.pen_number if each.pen_number else '', left)
                worksheet.write(r_no, c_no + 3, each.department_id.name, left)
                worksheet.write(r_no, c_no + 4, each.job_id.name, left)
                worksheet.write(r_no, c_no + 5, '\n'.join(pg_list), left)
                worksheet.write(r_no, c_no + 6, '\n'.join(net_list), left)
                worksheet.write(r_no, c_no + 7, '\n'.join(phd_list), left)
                worksheet.write(r_no, c_no + 8, '\n'.join(mphil_list), left)
                worksheet.write(r_no, c_no + 9, '\n'.join(add_pg_list), left)
                worksheet.write(r_no, c_no + 10, '\n'.join(other_list), left)
                worksheet.write(r_no, c_no + 11,
                                str(each.probation_date.strftime('%d/%m/%Y')) if each.probation_date else '', left)
                worksheet.write(r_no, c_no + 12, each.gender, left)
                worksheet.write(r_no, c_no + 13, str(service) + ' Years', left)
                worksheet.write(r_no, c_no + 14, each.religion_id.name if each.religion_id else '', left)
                worksheet.write(r_no, c_no + 15, each.caste_id.name if each.caste_id else '', left)
                worksheet.write(r_no, c_no + 16, each.address if each.address else '', left)
                worksheet.write(r_no, c_no + 17, each.constituency_id.name if each.constituency_id else '', left)
                worksheet.write(r_no, c_no + 19, each.mobile_phone if each.mobile_phone else '', left)
                worksheet.write(r_no, c_no + 20, each.mobile_phone if each.mobile_phone else '', left)
                worksheet.write(r_no, c_no + 21, each.work_phone if each.work_phone else '', left)
                worksheet.write(r_no, c_no + 22, each.work_email if each.work_email else '', left)
                worksheet.write(r_no, c_no + 23, each.aadhar_number if each.aadhar_number else '', left)
                worksheet.write(r_no, c_no + 24, each.pan_number if each.pan_number else '', left)
                worksheet.write(r_no, c_no + 25, str(each.birthday.strftime('%d/%m/%Y')) if each.birthday else '', left)
                worksheet.write(r_no, c_no + 26,
                                str(each.date_of_joining.strftime('%d/%m/%Y')) if each.date_of_joining else '', left)
                worksheet.write(r_no, c_no + 27, each.approval_order if each.approval_order else '', left)
                worksheet.write(r_no, c_no + 28,
                                str(each.approval_order_date.strftime('%d/%m/%Y')) if each.approval_order_date else '',
                                left)
                worksheet.write(r_no, c_no + 29, '', left)
                worksheet.write(r_no, c_no + 30, basic if basic > 0 else '', left)
                worksheet.write(r_no, c_no + 31, agp if agp > 0 else '', left)
                worksheet.write(r_no, c_no + 33, hra if hra > 0 else '', left)
                worksheet.write(r_no, c_no + 34, service_book.station_id.name if service_book else '', left)
                r_no += 1
            r_no += 1
            domain1.pop()

