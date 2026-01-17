# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import codecs
import jinja2
import json
import logging
import os
import sys
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response

_logger = logging.getLogger(__name__)

# if hasattr(sys, 'frozen'):
#     # When running on compiled windows binary, we don't have access to package loader.
path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
loader = jinja2.FileSystemLoader(path)
# else:
#     loader = jinja2.PackageLoader('fc_custom.fc_students', "views")
env = jinja2.Environment(loader=loader, autoescape=True)
env.filters["json"] = json.dumps


class HrIDCard(http.Controller):
    @http.route(['/hr/id_card/<string:employee>/<string:page>'], type="http", auth="user", website=True,
                method=['POST'],
                csrf=False)
    def example(self, employee, page):
        values = {}
        values['page'] = page
        employee_list = employee.split(',')
        employee_list = [int(i) for i in employee_list]
        data = request.env['hr.employee'].sudo().browse(employee_list)
        employee_list = []
        for each in data:
            employee_list.append({'hr': each, 'image': codecs.decode(each.image_1920) if each.image_1920 else ''})
        values['hrs'] = employee_list
        return env.get_template("hr_idcard.html").render(values)