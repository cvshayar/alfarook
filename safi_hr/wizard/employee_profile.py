from odoo import fields, models, api


class ModelName(models.TransientModel):
    _name = 'employee.profile'
    _description = 'Employee Profile'

    employee_ids = fields.Many2many('hr.employee')
    department_ids = fields.Many2many('hr.employee')

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'employee.profile', 'form': self.read()[0]}
        return self.env.ref('safi_hr.employee_profile_xlsx_id').report_action(self, data=datas, config=False)


class EmployeeProfileReportXlsx(models.AbstractModel):
    _name = 'report.safi_hr.employee_profile_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Employee Profile")

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
        worksheet.merge_range(2, 0, 7, 0, 'SL.No', boldc)
        worksheet.merge_range(2, 1, 7, 1, 'Name of \n Incumbent', boldc)
        worksheet.merge_range(2, 2, 7, 2, 'Department', boldc)
        worksheet.merge_range(2, 3, 7, 3, 'Designation', boldc)
        worksheet.merge_range(2, 5, 5, 10, 'Qualification (with date & class)', boldc)
        worksheet.merge_range(6, 5, 7, 5, '               PG              ', center)
        worksheet.merge_range(6, 6, 7, 6, 'NET', center)
        worksheet.merge_range(6, 7, 7, 7, 'PhD', center)
        worksheet.merge_range(6, 8, 7, 8, 'MPhil', center)
        worksheet.merge_range(6, 9, 7, 9, 'Additional \n PG', center)
        worksheet.merge_range(6, 10, 7, 10, 'Other', center)
        worksheet.merge_range(2, 11, 7, 11, 'Sex', boldc)
        worksheet.merge_range(2, 12, 7, 12, 'Length of \n Service', boldc)
        worksheet.merge_range(2, 13, 7, 13, 'Religion', boldc)
        worksheet.merge_range(2, 14, 7, 14, 'Caste', boldc)
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
