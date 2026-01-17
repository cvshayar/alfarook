import json
from odoo import fields, models, api
from odoo.exceptions import Warning, UserError
from datetime import datetime
from odoo import http
from odoo.http import request
import base64


class AdmissionStatusController(http.Controller):
    @http.route(['/admission/student/<string:date>'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def admission_register_form(self, date):
        values = {}
        student_list = []
        student_transfer_list = []
        student_tc_list = []
        students = request.env['student.student'].sudo().search([('date_of_admission', '>=', date)])
        student_transfers = request.env['student.transfer'].sudo().search([('transferred_date', '>=', date)])
        student_tcs = request.env['tc.issued.register'].sudo().search([('tc_issued_date', '>=', date)])
        for transfer in student_transfers:
            if transfer.from_batch_id.programme_id.is_self_finance == transfer.to_batch_id.programme_id.is_self_finance:
                transfer_vals = {
                    'admission_number': transfer.admission_number,
                    'from_batch': transfer.from_batch_id.start_year,
                    'from_programme': transfer.from_batch_id.programme_id.code,
                    'to_batch': transfer.to_batch_id.start_year,
                    'to_programme': transfer.to_batch_id.programme_id.code
                }
                student_transfer_list.append(transfer_vals)
        for tc in student_tcs:
            transfer_vals = {
                'admission_number': tc.admission_number,
            }
            student_tc_list.append(transfer_vals)
        for student in students:
            vals = {
                'name': student.name,
                'admission_number': student.admission_number,
                'batch': student.batch_id.start_year,
                'fee_category': student.fee_category_id.name,
                'second_language': student.second_language_id.name,
                'admission_category': student.admission_category_id.name,
                'semester': student.semester_id.name,
                'appno': student.app_no,
                'roll_no': student.roll_no,
                'reg_no': student.reg_no,
                'programme': student.programme_id.code,
                'dateofadmission': str(student.date_of_admission),
                'yearofadmission': student.year_of_admission,
                'roll_order': student.roll_order,
                'self_finance': student.self_finance,
                'index': student.index,
                'address': student.address,
                'gender': student.gender,
                'pin': student.pin,
                'dob': str(student.dob),
                'caste': student.caste_id.name,
                'religion': student.religion_id.name,
                'caste_category': student.caste_category_id.name,
                'bloodgroup': student.blood_group,
                'ph': student.ph,
                'tcissued': student.tc_issued,
                'phone': student.phone,
                'mobile': student.mobile,
                'email': student.email,
                'sports': student.sports
            }
            student_list.append(vals)
        # if students:
        values['students'] = student_list
        # if student_transfers:
        values['transfers'] = student_transfer_list
        # if student_tcs:
        values['tcs'] = student_tc_list
        return json.dumps(values)


class ExamController(http.Controller):
    @http.route(['/exam/<string:programme_code>/<string:year>'], type="http", auth="public", website=True,
                method=['POST'],
                csrf=False)
    def admission_register_form(self, programme_code, year):
        values = {}
        student_list = []
        student_transfer_list = []
        student_tc_list = []
        batch = request.env['batch.batch'].sudo().search(
            [('programme_id.code', '=', programme_code), ('start_year', '=', year)])
        students = request.env['student.student'].sudo().search([('batch_id', '=', batch.id)])
        for student in students:
            vals = {
                'name': student.name,
                'admission_number': student.admission_number,
                'batch': student.batch_id.start_year,
                'fee_category': student.fee_category_id.name,
                'second_language': student.second_language_id.name,
                'admission_category': student.admission_category_id.name,
                'semester': student.semester,
                'appno': student.appno,
                'roll_no': student.roll_no,
                'reg_no': student.reg_no,
                'programme': student.programme_id.code,
                'dateofadmission': str(student.date_of_admission),
                'yearofadmission': student.year_of_admission,
                'roll_order': student.roll_order,
                'self_finance': student.self_finance,
                'index': student.index,
                'address': student.address,
                'post': student.post,
                'city': student.city,
                'district': student.district_id.name,
                'state': student.state_id.name,
                'nationality': student.nationality.name,
                'gender': student.gender,
                'pin': student.pin,
                'dob': str(student.dob),
                'caste': student.caste_id.name,
                'religion': student.religion_id.name,
                'caste_category': student.caste_category_id.name,
                'bloodgroup': student.blood_group,
                'ph': student.ph,
                'tcissued': student.tc_issued,
                'phone': student.phone,
                'mobile': student.mobile,
                'email': student.email,
                'sports': student.sports,
                'parent_name': student.parent_name,
                'parent_mobile': student.parent_mobile,
                'parent_email': student.parent_email,
                'aadhar': student.aadhar_number,
                'image': student.image.decode('utf-8')
            }
            student_list.append(vals)
        values['students'] = student_list
        return json.dumps(values)


class AdmissionStatusController(http.Controller):
    @http.route(['/admission/student/status/<string:app_no>/<string:year>/<string:level>'], type="http", auth="public",
                website=True, method=['POST'],
                csrf=False)
    def admission_register_form(self, app_no, year, level):
        values = {}
        student = request.env['student.student'].sudo().search(['|', ('active', '=', False), ('active', '=', True),
                                                                ('app_no', '=', app_no),
                                                                ('year_of_admission', '=', int(year)),
                                                                ('programme_id.level', '=', level)])
        if student:
            values['admitted'] = 'Yes'
        else:
            values['admitted'] = 'No'
        return json.dumps(values)
