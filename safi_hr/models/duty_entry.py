from odoo import fields, models, api
from odoo.exceptions import Warning, UserError


class InternalDutyType(models.Model):
    _name = 'internal.duty.type'
    _description = 'Internal Duty Type'

    name = fields.Char()


class DutyEntry(models.Model):
    _name = 'hr.internal.duty'
    _description = 'Internal Duty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    @api.model
    def get_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
        return employee

    employee_id = fields.Many2one('hr.employee', track_visibility='onchange', default=get_employee)
    department_id = fields.Many2one('hr.department', track_visibility='onchange')
    duty_type_id = fields.Many2one('internal.duty.type', track_visibility='onchange')
    date = fields.Date(default=fields.Date.today(), track_visibility='onchange')
    type = fields.Selection([('full_day', 'Full Day'), ('morning', 'Morning'), ('after_noon', 'After Noon'), ('hours', 'Hours')], track_visibility='onchange')
    hours = fields.Char(track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft', track_visibility='onchange')

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'full_day':
            self.hours = '1,2,3,4,5,6'
        elif self.type == 'morning':
            self.hours = '1,2,3'
        elif self.type == 'after_noon':
            self.hours = '4,5,6'
        else:
            self.hours = ''

    def confirm_duty(self):
        self.state = 'confirm'

    def unlink(self):
        for each in self:
            if each.state == 'confirm':
                raise UserError(str('You are not allowed to delete'))
            return super(DutyEntry, self).unlink()



