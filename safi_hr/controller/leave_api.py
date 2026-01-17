import json
from odoo import fields, models, api
from odoo.exceptions import Warning, UserError
import datetime
from odoo import http
from odoo.http import request


class LeaveStatusController(http.Controller):
    @http.route(['/employee/<string:email>/<string:date>'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def fetch_employee_status(self, email, date):
        values = {}
        employee = request.env['hr.employee'].sudo().search([('user_id.login', '=', email)])
        employee_leave = request.env['hr.leave'].sudo().search(
            [('employee_id', '=', employee.id), ('request_date_from', '<=', date), ('request_date_to', '>=', date), ('state', 'not in', ['cancel', 'refuse'])])
        if employee_leave.request_unit_half and employee_leave.request_date_from_period == 'am':
            leave_status = 'FN'
        if employee_leave.request_unit_half and employee_leave.request_date_from_period == 'pm':
            leave_status = 'AN'
        if not employee_leave.request_unit_half and employee_leave:
            leave_status = 'FL'
        if not employee_leave:
            leave_status = 'NL'
        values = {
            'email': email,
            'leave_status': leave_status,
            'date': date
        }
        return json.dumps(values)


class MonthlyLeaveStatusController(http.Controller):
    @http.route(['/employee/<string:email>/<string:from_date>/<string:to_date>'], type="http", auth="public",
                website=True, method=['POST'],
                csrf=False)
    def fetch_employee_status(self, email, from_date, to_date):
        values = {}
        employee = request.env['hr.employee'].sudo().search([('user_id.login', '=', email)])
        date1 = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
        date2 = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()
        day = datetime.timedelta(days=1)
        date_list = [date1]
        employee_leaves = []
        while date1 <= date2 - day:
            date1 = date1 + day
            date_list.append(date1)
        for each in date_list:
            employee_leave = request.env['hr.leave'].sudo().search(
                [('employee_id', '=', employee.id), ('request_date_from', '<=', each), ('request_date_to', '>=', each), ('state', 'not in', ['cancel', 'refuse'])])
            if employee_leave.request_unit_half and employee_leave.request_date_from_period == 'am':
                leave_status = 'FN'
            if employee_leave.request_unit_half and employee_leave.request_date_from_period == 'pm':
                leave_status = 'AN'
            if not employee_leave.request_unit_half and employee_leave:
                leave_status = 'FL'
            if not employee_leave:
                leave_status = 'NL'
            if employee_leave:
                if each.strftime('%A') not in ['Sunday', 'Saturday']:
                    values = {
                        'email': email,
                        'leave_status': leave_status,
                        'date': each.strftime('%Y-%m-%d'),
                        'leave_type': employee_leave.holiday_status_id.name
                    }
                    employee_leaves.append(values)
        return json.dumps(employee_leaves)
