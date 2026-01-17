import json

from odoo import http
from odoo.http import request
from werkzeug.utils import redirect


class AttendanceConnector(http.Controller):
    @http.route('/attendance', type='http', auth='user', website=True)
    def attendance_connector_page(self, **kw):
        odoo_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        attendance_api_url = http.request.env['ir.config_parameter'].sudo().get_param('attendance_api_url')
        hr = http.request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)])
        url = '%s/attendance/' % attendance_api_url
        if request.env.user.login == 'principal':
            url = '%s/attendance/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=p&rurl=%s' % (
                attendance_api_url, request.env.user.login, request.env.user.login, odoo_url)
        if hr and request.env.user.login != 'principal':
            if hr['employee_type'] == 'teaching':
                url = '%s/attendance/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=f&rurl=%s' % (
                    attendance_api_url, hr['user_id']['login'], hr['user_id']['login'], odoo_url)
            if hr['employee_type'] == 'non_teaching':
                url = '%s/attendance/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=o&rurl=%s' % (
                    attendance_api_url, hr['user_id']['login'], hr['user_id']['login'], odoo_url)
        if not hr and request.env.user.login != 'principal':
            url = '%s/attendance/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=o&rurl=%s' % (
                attendance_api_url, request.env.user.login, request.env.user.login, odoo_url)
        return redirect(url)


class ApplicationConnector(http.Controller):
    @http.route('/application', type='http', auth='user', website=True)
    def application_connector_page(self, **kw):
        odoo_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        application_api_url = http.request.env['ir.config_parameter'].sudo().get_param('application_api_url')
        hr = http.request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)])
        url = '%s/' % application_api_url
        if request.env.user.login == 'principal':
            url = '%s/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=p&rurl=%s' % (
                application_api_url, request.env.user.login, request.env.user.login, odoo_url)
        else:
            url = '%s/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=o&rurl=%s' % (
                application_api_url, request.env.user.login, request.env.user.login, odoo_url)
        # if hr and request.env.user.login != 'principal':
        #     if hr['employee_type'] == 'teaching':
        #         url = '%s/attendance/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=f&rurl=%s' % (
        #             application_api_url, hr['user_id']['login'], hr['user_id']['login'], odoo_url)
        #     if hr['employee_type'] == 'non_teaching':
        #         url = '%s/attendance/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=o&rurl=%s' % (
        #             application_api_url, hr['user_id']['login'], hr['user_id']['login'], odoo_url)
        # if not hr and request.env.user.login != 'principal':
        #     url = '%s/attendance/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=o&rurl=%s' % (
        #         application_api_url, request.env.user.login, request.env.user.login, odoo_url)
        return redirect(url)


# class ExamController(http.Controller):
#     @http.route('/exam', type='http', auth='public', website=True)
#     def render_exam_page(self, **kw):
#         odoo_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
#         hr = http.request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)])
#         url = 'https://fcexams.in/auto_auth.php?u=%s&p=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&t=f&rurl=%s' % (
#             hr['user_id']['login'], hr['user_id']['login'], odoo_url)
#         return redirect(url)

