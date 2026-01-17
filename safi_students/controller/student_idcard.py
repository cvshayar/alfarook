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

path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'controller'))
loader = jinja2.FileSystemLoader(path)
env = jinja2.Environment(loader=loader, autoescape=True)
env.filters["json"] = json.dumps


class StudentIDCard(http.Controller):
    @http.route(['/student/id_card/<string:student>/<string:page>'], type="http", auth="user", website=True,
                method=['POST'],
                csrf=False)
    def example(self, student, page):
        values = {'page': page}
        student_list = student.split(',')
        student_list = [int(i) for i in student_list]
        data = request.env['student.student'].sudo().search([('admission_number', 'in', student_list)],
                                                            order='roll_order ASC')
        student_list = []
        for each in data:
            student_list.append({'student': each, 'image': codecs.decode(each.image) if each.image else ''})
        values['students'] = student_list
        return env.get_template("student_id_page.html").render(values)
