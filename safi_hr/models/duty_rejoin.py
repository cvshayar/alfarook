from odoo import fields, models, api
from odoo.exceptions import Warning, UserError


class DutyRejoin(models.Model):
    _name = 'duty.rejoin'
    _description = 'Description'

    def get_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        return employee

    name = fields.Char(compute='compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', required=True, default=get_employee)
    date = fields.Date('Rejoin Date', required=True)
    duty_certificate_ids = fields.Many2many('ir.attachment')
    leave_id = fields.Many2one('hr.leave')
    read_bool = fields.Boolean()

    @api.model
    def create(self, values):
        # Add code here
        values['read_bool'] = True
        # raise UserError(str(values['duty_certificate_ids'][0][1]))
        # if not values['duty_certificate_ids'][0][1]:
        #     raise UserError(str('Attach your Duty Certificate'))
        return super(DutyRejoin, self).create(values)

    @api.depends('employee_id', 'date')
    def compute_name(self):
        for each in self:
            each.name = str(each.employee_id.name) + ' ' + str(each.date.strftime('%d/%m/%Y'))

    @api.onchange('employee_id')
    def fc_onchange_employee_id(self):
        if self.employee_id:
            leave_list = []
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', self.employee_id.id), ('holiday_status_id.is_duty', '=', True),
                 ('state', '=', 'validate')])
            for leave in leaves:
                rejoin = self.env['duty.rejoin'].search(
                    [('employee_id', '=', self.employee_id.id), ('leave_id', '=', leave.id)])
                if rejoin:
                    leave_list.append(rejoin.leave_id.id)
            # raise UserError(str(leave_list))

            leave_domain = [('employee_id', '=', self.employee_id.id), ('holiday_status_id.is_duty', '=', True),
                            ('id', 'not in', leave_list), ('state', '=', 'validate')]
            return {'domain': {'leave_id': leave_domain}}
