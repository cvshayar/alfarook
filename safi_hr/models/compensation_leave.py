from odoo import fields, models, api
from datetime import date


class ModelName(models.Model):
    _name = 'compensation.leave'
    _description = 'Compensation Leave'

    @api.model
    def get_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id

    name = fields.Char(compute='get_name')
    employee_id = fields.Many2one('hr.employee', default=get_employee)
    from_date = fields.Date(default=fields.Date.today())
    to_date = fields.Date(default=fields.Date.today())
    remarks = fields.Text()
    number_of_days = fields.Integer()
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft')

    @api.onchange('from_date', 'to_date')
    def get_number_of_days(self):
        if self.from_date and self.to_date:
            difference = self.to_date - self.from_date
            self.number_of_days = difference.days + 1

    def confirm_compensation_leave(self):
        holiday_status_id = self.env['hr.leave.type'].search([('validity_start', '<=', self.from_date), ('validity_stop', '>=', self.to_date), ('is_compensation', '=', True)])
        values = {
            'employee_id': self.employee_id.id,
            'holiday_type': 'employee',
            'name': '%s of %s' % (holiday_status_id.name, self.employee_id.name),
            'holiday_status_id': holiday_status_id.id,
            'number_of_days_display': self.number_of_days
        }
        leave_allocation = self.env['hr.leave.allocation'].create(values)
        leave_allocation.action_approve()
        self.state = 'confirm'

    @api.depends('employee_id', 'from_date')
    def get_name(self):
        for each in self:
            each.name = '%s - %s' % (each.employee_id.name, each.from_date.strftime('%d/%m/%Y'))


