from odoo import fields, models, api


class ScholarshipReport(models.TransientModel):
    _name = 'scholarship.report'
    _description = 'Scholarship Report'

    from_date = fields.Date()
    to_date = fields.Date()
    scholarship_ids = fields.Many2many('scholarship.scholarship')

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'scholarship.report', 'form': self.read()[0]}
        return self.env.ref('safi_students.scholarship_report_xlsx_id').report_action(self, data=datas,
                                                                                      config=False)


class DetailedAdmissionSummaryXlsx(models.AbstractModel):
    _name = 'report.safi_students.scholarship_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Scholarship")

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
        worksheet.merge_range(0, 0, 0, 8, self.env.company.name, boldc)
        worksheet.merge_range(1, 0, 1, 8, 'Scholarship Details', boldc)
        worksheet.write(2, 0, 'SI', boldc)
        worksheet.write(2, 1, 'Name', boldc)
        worksheet.write(2, 2, 'Admission Number', boldc)
        worksheet.write(2, 3, 'Batch', boldc)
        worksheet.write(2, 4, 'Semester', boldc)
        worksheet.write(2, 5, 'Scholarship', boldc)
        worksheet.write(2, 6, 'Amount', boldc)
        worksheet.write(2, 7, 'Date', boldc)
        worksheet.write(2, 8, 'Remarks', boldc)
        row = 3
        domain = []
        if invoices.from_date:
            domain.append(('date', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('date', '<=', invoices.to_date))
        if invoices.scholarship_ids:
            domain.append(('scholarship_id', 'in', invoices.scholarship_ids.ids))
        scholarship_details = self.env['scholarship.details'].search(domain)
        i = 0
        total = 0
        for scholarship_detail in scholarship_details:
            total += scholarship_detail.amount
            i += 1
            worksheet.write(row, 0, i, left)
            worksheet.write(row, 1, scholarship_detail.student_id.name, left)
            worksheet.write(row, 2, scholarship_detail.admission_number, left)
            worksheet.write(row, 3, scholarship_detail.batch_id.complete_name, left)
            worksheet.write(row, 4, scholarship_detail.semester.name, left)
            worksheet.write(row, 5, scholarship_detail.scholarship_id.name, left)
            worksheet.write(row, 6, scholarship_detail.amount, right)
            worksheet.write(row, 7, scholarship_detail.date.strftime('%d/%m/%Y') if scholarship_detail.date else '',
                            center)
            worksheet.write(row, 8, scholarship_detail.remarks if scholarship_detail.remarks else '', left)
            row += 1
        worksheet.merge_range(row, 0, row, 5, 'Total', boldc)
        worksheet.write(row, 6, total, boldc)
