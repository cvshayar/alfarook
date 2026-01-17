from odoo import fields, models, api


class AttendanceSummaryReport(models.Model):
    _name = 'attendance.summary.report'
    _description = 'Attendance Summary Report'

    start_year = fields.Integer(default=fields.Date.today().year)
    semester_id = fields.Many2one('semester.semester')
    from_date = fields.Date()
    to_date = fields.Date()

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'attendance.summary.report', 'form': self.read()[0]}
        return self.env.ref('safi_students.attendance_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                             config=False)


class AttendanceSummaryReportXlsx(models.AbstractModel):
    _name = 'report.safi_students.attendance_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Attendance Summary Report")

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
        worksheet.merge_range(0, 0, 1, 2, self.env.company.name, boldc)
        worksheet.write(2, 0, 'SI', boldc)
        worksheet.write(2, 1, 'Batch', boldc)
        worksheet.write(2, 2, 'Attendance %', boldc)
        domain = []
        if invoices.from_date:
            domain.append(('date', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date', '<=', invoices.to_date))
        if invoices.start_year:
            domain.append(('student_id.batch_id.start_year', '=', invoices.start_year))
        if invoices.semester_id:
            domain.append(('student_id.semester_id', '=', invoices.semester_id.id))
        student_attendance = self.env['student.attendance'].search(domain, order='date ASC')
        batches = student_attendance.mapped('student_id.batch_id')
        row = 3
        i = 0
        for batch in batches:
            total_present = 0
            total_absent = 0
            total = 0
            i += 1
            batch_attendance = student_attendance.filtered(lambda x: x.student_id.batch_id.id == batch.id)
            for each in batch_attendance:
                if each.hour_1 == 'X':
                    total_present += 1
                if each.hour_1 == 'A':
                    total_absent += 1
                if each.hour_2 == 'X':
                    total_present += 1
                if each.hour_2 == 'A':
                    total_absent += 1
                if each.hour_3 == 'X':
                    total_present += 1
                if each.hour_3 == 'A':
                    total_absent += 1
                if each.hour_4 == 'X':
                    total_present += 1
                if each.hour_4 == 'A':
                    total_absent += 1
                if each.hour_5 == 'X':
                    total_present += 1
                if each.hour_5 == 'A':
                    total_absent += 1
            total = total_present + total_absent
            worksheet.write(row, 0, i, center)
            worksheet.write(row, 1, batch.complete_name, left)
            worksheet.write(row, 2, round((total_present*100)/total, 2), right)
            # worksheet.write(row, 3, total_present, right)
            # worksheet.write(row, 4, total_absent, right)
            row += 1

