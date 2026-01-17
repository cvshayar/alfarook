from odoo import fields, models, api


class StudentAttendanceReport(models.TransientModel):
    _name = 'student.attendance.report'
    _description = 'StudentAttendanceReport'

    from_date = fields.Date()
    to_date = fields.Date()
    batch_id = fields.Many2one('batch.batch')
    semester_id = fields.Many2one('semester.semester')
    student_id = fields.Many2one('student.student')

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'student.fee.due', 'form': self.read()[0]}
        return self.env.ref('safi_students.student_attendance_report_xlsx_id').report_action(self, data=datas,
                                                                                             config=False)
        
        
class StudentAttendanceAbsenteeReport(models.TransientModel):
    _name = 'student.attendance.absentee.report'
    _description = 'StudentAttendanceAbsenteeReport'

    from_date = fields.Date()
    to_date = fields.Date()
    batch_id = fields.Many2one('batch.batch')
    semester_id = fields.Many2one('semester.semester')

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'sstudent.attendance.absentee.report', 'form': self.read()[0]}
        return self.env.ref('safi_students.student_attendance_absentee_report_xlsx_id').report_action(self, data=datas,
                                                                                             config=False)


class StudentAttendanceReportXlsx(models.AbstractModel):
    _name = 'report.safi_students.student_attendance_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Attendance Report")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        boldr = workbook.add_format({'bold': True, 'align': 'right', 'border': 1})
        boldl = workbook.add_format({'bold': True, 'align': 'left', 'border': 1})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center', 'border': 1})
        right = workbook.add_format({'align': 'right', 'border': 1})
        left = workbook.add_format({'align': 'left', 'border': 1})
        center_red = workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'red'})
        boldc.set_align('vcenter')
        boldr.set_align('vcenter')
        boldl.set_align('vcenter')
        center.set_align('vcenter')
        left.set_align('vcenter')
        right.set_align('vcenter')
        center_red.set_align('vcenter')
        row = 2
        domain = []
        if invoices.from_date:
            domain.append(('date', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date', '<=', invoices.to_date))
        if invoices.batch_id:
            domain.append(('student_id.batch_id', '=', invoices.batch_id.id))
        if invoices.semester_id:
            domain.append(('semester_id', '=', invoices.semester_id.id))
        if invoices.student_id:
            domain.append(('student_id', '=', invoices.student_id.id))
        student_attendance = self.env['student.attendance'].search(domain, order='date ASC')
        dates = list(set(student_attendance.mapped('date')))
        dates.sort()
        if not invoices.student_id:
            worksheet.merge_range(0, 0, 1, len(dates) * 5 + 4, self.env.company.name, boldc)
            i = 1
            worksheet.merge_range(row, 0, row + 1, 0, 'Admission\nNumber', boldc)
            worksheet.merge_range(row, 1, row + 1, 1, 'Name', boldc)
            worksheet.merge_range(row, 2, row + 1, 2, 'Roll\nNumber', boldc)
            col = 3
            for date in dates:
                worksheet.merge_range(row, col, row, col + 4, date.strftime('%d/%m/%Y'), boldc)
                worksheet.write(row + 1, col, '1', boldc)
                worksheet.write(row + 1, col + 1, '2', boldc)
                worksheet.write(row + 1, col + 2, '3', boldc)
                worksheet.write(row + 1, col + 3, '4', boldc)
                worksheet.write(row + 1, col + 4, '5', boldc)
                col += 5
            worksheet.merge_range(row, col, row + 1, col, 'Total', boldc)
            worksheet.merge_range(row, col + 1, row + 1, col + 1, '%', boldc)
            students = self.env['student.student'].search([('batch_id', '=', invoices.batch_id.id)], order='name')
            row += 1
            for student in students:
                row += 1
                worksheet.write(row, 0, student.admission_number, left)
                worksheet.write(row, 1, student.name, left)
                worksheet.write(row, 2, student.roll_no, left)
                col = 3
                total_hour = 0
                total_present = 0
                for date in dates:
                    attendance = student_attendance.filtered(lambda x: x.date == date and x.student_id.id == student.id)
                    if attendance.hour_1 != 'N':
                        total_hour += 1
                    if attendance.hour_2 != 'N':
                        total_hour += 1
                    if attendance.hour_3 != 'N':
                        total_hour += 1
                    if attendance.hour_4 != 'N':
                        total_hour += 1
                    if attendance.hour_5 != 'N':
                        total_hour += 1
                    if attendance.hour_1 == 'X':
                        total_present += 1
                    if attendance.hour_2 == 'X':
                        total_present += 1
                    if attendance.hour_3 == 'X':
                        total_present += 1
                    if attendance.hour_4 == 'X':
                        total_present += 1
                    if attendance.hour_5 == 'X':
                        total_present += 1
                    worksheet.write(row, col, attendance.hour_1 if attendance.hour_1 != 'N' else '',
                                    center if attendance.hour_1 != 'A' else center_red)
                    worksheet.write(row, col + 1, attendance.hour_2 if attendance.hour_2 != 'N' else '',
                                    center if attendance.hour_2 != 'A' else center_red)
                    worksheet.write(row, col + 2, attendance.hour_3 if attendance.hour_3 != 'N' else '',
                                    center if attendance.hour_3 != 'A' else center_red)
                    worksheet.write(row, col + 3, attendance.hour_4 if attendance.hour_4 != 'N' else '',
                                    center if attendance.hour_4 != 'A' else center_red)
                    worksheet.write(row, col + 4, attendance.hour_5 if attendance.hour_5 != 'N' else '',
                                    center if attendance.hour_5 != 'A' else center_red)
                    col += 5
                worksheet.write(row, col, total_hour, boldc)
                worksheet.write(row, col + 1, round((total_present / total_hour) * 100, 2), boldr)
        else:
            worksheet.merge_range(0, 0, 1, 23, self.env.company.name, boldc)
            worksheet.merge_range(2, 0, 2, 23, 'Attendance Report', boldc)
            worksheet.merge_range(3, 0, 3, 23, 'Admission No : %s | Name : %s  | Batch : %s  |  Period : %s - %s' % (
                invoices.student_id.admission_number, invoices.student_id.name, invoices.batch_id.complete_name,
                invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
            # worksheet.write(3, 0, )
            i = 0
            date_values = {}
            date_list = []
            for date in dates:
                i += 1
                attendance = student_attendance.filtered(lambda x: x.date == date)
                if i <= 4:
                    date_values.update({'%s\n%s' % (date.strftime('%d/%m/%y'), date.strftime('%a')): attendance})
                if i == 4:
                    date_list.append(date_values)
                    date_values = {}
                    i = 0
            if i < 4:
                date_list.append(date_values)
            row = 4
            col = 0
            for i in range(0, 4):
                worksheet.write(row, col, 'Date', boldc)
                worksheet.write(row, col + 1, 'H1', boldc)
                worksheet.write(row, col + 2, 'H2', boldc)
                worksheet.write(row, col + 3, 'H3', boldc)
                worksheet.write(row, col + 4, 'H4', boldc)
                worksheet.write(row, col + 5, 'H5', boldc)
                col += 6
            for dates in date_list:
                row += 1
                col = 0
                for key, value in dates.items():
                    worksheet.write(row, col, key, center)
                    worksheet.write(row, col + 1, value.hour_1 if value.hour_1 != 'N' else '',
                                    center if value.hour_1 != 'A' else center_red)
                    worksheet.write(row, col + 2, value.hour_2 if value.hour_2 != 'N' else '',
                                    center if value.hour_2 != 'A' else center_red)
                    worksheet.write(row, col + 3, value.hour_3 if value.hour_3 != 'N' else '',
                                    center if value.hour_3 != 'A' else center_red)
                    worksheet.write(row, col + 4, value.hour_4 if value.hour_4 != 'N' else '',
                                    center if value.hour_4 != 'A' else center_red)
                    worksheet.write(row, col + 5, value.hour_5 if value.hour_5 != 'N' else '',
                                    center if value.hour_5 != 'A' else center_red)
                    col += 6
                    
                
                
# Absentee List

class StudentAttendanceAbsenteeReportXlsx(models.AbstractModel):
    _name = 'report.safi_students.student_attendance_absentee_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Attendance Absentee Report")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        boldr = workbook.add_format({'bold': True, 'align': 'right', 'border': 1})
        boldl = workbook.add_format({'bold': True, 'align': 'left', 'border': 1})
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center', 'border': 1})
        right = workbook.add_format({'align': 'right', 'border': 1})
        left = workbook.add_format({'align': 'left', 'border': 1})
        center_red = workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'red'})
        boldc.set_align('vcenter')
        boldr.set_align('vcenter')
        boldl.set_align('vcenter')
        center.set_align('vcenter')
        left.set_align('vcenter')
        right.set_align('vcenter')
        center_red.set_align('vcenter')
        row = 3
        domain = []
        if invoices.from_date:
            domain.append(('date', '=', invoices.from_date))
        # if invoices.to_date:
        #     domain.append(('date', '<=', invoices.to_date))
        if invoices.batch_id:
            domain.append(('student_id.batch_id', '=', invoices.batch_id.id))
        if invoices.semester_id:
            domain.append(('semester_id', '=', invoices.semester_id.id))
        student_attendance = self.env['student.attendance'].search(domain, order='date ASC').filtered(
            lambda x: x.hour_1 == 'A' or x.hour_2 == 'A' or x.hour_3 == 'A' or x.hour_4 == 'A' or x.hour_5 == 'A' or x.hour_6 == 'A')
        students = student_attendance.mapped('student_id')
        sorted_students = sorted(students, key=lambda student: student.name)
        # dates = list(set(student_attendance.mapped('date')))
        # dates.sort()
        # if not invoices.student_id:
        worksheet.merge_range(0, 0, 1, 4, self.env.company.name, boldc)
        worksheet.merge_range(2, 0, 2, 4, 'Date : %s' % (invoices.from_date.strftime('%d/%m/%Y')), boldc)
        i = 1
        worksheet.merge_range(row, 0, row + 1, 0, 'Name', boldc)
        worksheet.merge_range(row, 1, row + 1, 1, 'Admission\nNumber', boldc)
        worksheet.merge_range(row, 2, row + 1, 2, 'Roll\nNumber', boldc)
        worksheet.merge_range(row, 3, row + 1, 3, 'Batch', boldc)
        worksheet.merge_range(row, 4, row + 1, 4, 'Hour', boldc)
        # worksheet.merge_range(row, 5, row + 1, 5, 'Hour 2', boldc)
        # worksheet.merge_range(row, 6, row + 1, 6, 'Hour 3', boldc)
        # worksheet.merge_range(row, 7, row + 1, 7, 'Hour 4', boldc)
        # worksheet.merge_range(row, 8, row + 1, 8, 'Hour 5', boldc)
        # worksheet.merge_range(row, 9, row + 1, 9, 'Hour 6', boldc) 
        row = 4
        for student in sorted_students:
            row += 1
            absent_list = []
            absent_hours = student_attendance.filtered(lambda x: x.student_id.id == student.id)
            if absent_hours.filtered(lambda x: x.hour_1 == 'A'):
                absent_list.append('1')
            if absent_hours.filtered(lambda x: x.hour_2 == 'A'):
                absent_list.append('2')
            if absent_hours.filtered(lambda x: x.hour_3 == 'A'):
                absent_list.append('3')
            if absent_hours.filtered(lambda x: x.hour_4 == 'A'):
                absent_list.append('4')
            if absent_hours.filtered(lambda x: x.hour_5 == 'A'):
                absent_list.append('5')
            if absent_hours.filtered(lambda x: x.hour_6 == 'A'):
                absent_list.append('6')
            worksheet.write(row, 0, student.name, left)
            worksheet.write(row, 1, student.admission_number, left)
            worksheet.write(row, 2, student.roll_no, left)
            worksheet.write(row, 3, student.batch_id.complete_name, left)
            worksheet.write(row, 4, ','.join(absent_list), left)
            

