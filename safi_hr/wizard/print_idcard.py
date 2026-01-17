from odoo import fields, models, api
from datetime import datetime, date, timedelta


class EmployeeIDCardWizard(models.TransientModel):
    _name = 'employee.idcard.wizard'
    _description = 'Employee ID Card'

    employee_ids = fields.Many2many('hr.employee')
    print = fields.Selection([('front', 'Front'), ('back', 'Back'), ('both', 'Both')], default='front')

    def print_id_card(self):
        employee_list = []
        for each in self.employee_ids:
            employee_list.append(str(each.id))
        employees = ','.join(employee_list)
        return {
            'type': 'ir.actions.act_url',
            'url': 'hr/id_card/%s/%s' % (employees, self.print),
            'target': 'new'
        }
