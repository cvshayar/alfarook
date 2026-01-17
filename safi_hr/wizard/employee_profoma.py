from odoo import fields, models, api
from datetime import datetime, date, timedelta


class EmployeeProformaWizard(models.TransientModel):
    _name = 'employee.proforma'
    _description = 'Description'
    staff_type = fields.Selection([('teaching', 'Teaching'), ('non_teaching', 'Non Teaching')])
    date = fields.Date()
    report_type = fields.Selection([('Qualification', 'Qualification'), ('Religion', 'Religion'), ('Caste', 'Caste')])
    qualification_ids = fields.Many2many('qualification.level')
    religion_ids = fields.Many2many('hr.religion')
    caste_ids = fields.Many2many('hr.caste')
    from_date = fields.Date()
    to_date = fields.Date()

    # model_ids = fields.Many2many('ir.model.fields', domain=[('model_id', '=', 158)])

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'employee.proforma', 'form': self.read()[0]}
        if self.report_type == 'Qualification':
            return self.env.ref('safi_hr.employee_qualification_xlsx_id').report_action(self, data=datas, config=False)
        elif self.report_type == 'Religion':
            return self.env.ref('safi_hr.employee_religion_xlsx_id').report_action(self, data=datas, config=False)
        elif self.report_type == 'Caste':
            return self.env.ref('safi_hr.employee_caste_xlsx_id').report_action(self, data=datas, config=False)
        else:
            return self.env.ref('safi_hr.employee_proforma_xlsx_id').report_action(self, data=datas, config=False)



