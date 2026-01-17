from odoo import fields, models, api
from datetime import datetime, date, timedelta


class EmployeePublicationReport(models.TransientModel):
    _name = 'employee.publication.report'
    _description = 'Description'

    employee_ids = fields.Many2many('hr.employee')

    def generate_report(self):
        data = {'model_id': self.id, 'employee_ids': self.employee_ids.ids}
        return self.env.ref('safi_hr.employee_publication_pdf_id').report_action(self, data=data)


class EmployeePublicationReportPdf(models.Model):
    _name = 'report.safi_hr.employee_publication_pdf'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        employees = self.env['hr.employee'].search([('id', 'in', data['employee_ids'])])
        lines = []
        for employee in employees:
            qualifications = self.env['hr.qualification'].search([('employee_id', '=', employee.id)])
            publications = self.env['employee.publications'].search([('employee_id', '=', employee.id)])
            inservices = self.env['employee.inservice'].search([('employee_id', '=', employee.id)])
            committees = self.env['employee.committee'].search([('employee_id', '=', employee.id)])
            lines.append({
                'employee': employee,
                'qualifications': qualifications,
                'publications': publications,
                'inservices': inservices,
                'committees': committees
            })
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': lines,
        }