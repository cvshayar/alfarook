from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError


class AdmissionRegisterWizard(models.TransientModel):
    _name = 'admission.register.report'

    year_of_admission = fields.Integer(default=fields.Date.today().year)
    type = fields.Selection([('aided', 'Aided'), ('self_finance', 'Self finance')], default='self_finance')

    # def print_excel_report(self):
    #     domain = [('year_of_admission', '=', self.year_of_admission)]
    #     record_ids = self.env['student.student'].sudo().search(domain)
    #     if len(record_ids) == 0:
    #         raise UserError("Records does not exist!!!")
    #     context = self._context
    #     datas = {'ids': context.get('active_ids', []), 'model': 'student.report.wizard', 'form': self.read()[0]}
    #     return self.env.ref('safi_students.admission_register_report_xlsx_id').report_action(self, data=datas,
    #                                                                                          config=False)

    def generate_report(self):
        data = {'model_id': self.id, 'year_of_admission': self.year_of_admission, 'type': self.type}
        return self.env.ref('safi_students.admission_register_report_pdf_id').report_action(self, data=data)


# PDF
class AdmissionRegisterPdf(models.Model):
    _name = 'report.safi_students.admission_register_report_pdf'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        lines = []
        domain = ['|', ('active', '=', False), ('active', '=', True), ('admission_number', '!=', 0)]
        if data['year_of_admission']:
            domain.append(('year_of_admission', '=', data['year_of_admission']))
        if data['type'] == 'aided':
            course_type = False
        else:
            course_type = True
        domain.append(('self_finance', '=', course_type))
        for student in self.env['student.student'].sudo().search(domain, order='admission_number'):
            parent = []
            if student.parent_address:
                parent_address = student.parent_address
                parent_address = parent_address.replace(',,,', ', ')
                parent_address = parent_address.replace(',,', ', ')
                parent_address = parent_address.replace(', ,', ', ')
                parent_address = parent_address.replace(',', ', ')
                parent_address = parent_address.replace(',,', ', ')
                parent_address = parent_address.replace('\n', ' ')
                parent_address = parent_address.replace('   ', ' ')
                parent_address = parent_address.replace('  ', ' ')
                address = [parent_address[i: i + 22] for i in range(0, len(parent_address), 22)]
                parent_address = '\n'.join(address)
            if student.parent_name:
                job = student.parent_job if student.parent_job else ''
                parent.append(student.parent_name.upper() + ', ' + str(job.upper()))
            if student.parent_address:
                parent.append(parent_address.upper())
            if student.parent_mobile:
                parent.append('Ph: ' + student.parent_mobile)
            if student.programme_id.level in ['ug', 'integrated']:
                school = student.plus2_school.upper() if student.plus2_school else ''
            else:
                school = student.college.upper() if student.college else ''
            school = [school[i: i + 13] for i in range(0, len(school), 13)]
            school = '\n'.join(school)
            if student.place_of_birth:
                place_of_birth = [student.place_of_birth[i: i + 10] for i in range(0, len(student.place_of_birth), 10)]
                place_of_birth = '\n'.join(place_of_birth)
            if student.programme_id.level == 'ug':
                programme = 'UG Course-\n' + str(student.programme_id.name.upper())
            else:
                programme = 'PG Course-\n' + str(student.programme_id.name.upper())
            vals = {
                'admission_no': student.admission_number,
                'name': student.name.upper(),
                'birth_place': place_of_birth.upper() if student.place_of_birth else '',
                'dob': student.dob.strftime('%d/%m/%Y') if student.dob else '',
                'parent_details': parent,
                'religion': student.religion_id.name.upper() if student.religion_id else '',
                'caste': student.caste_id.name,
                'school': school,
                'admission_date': student.date_of_admission.strftime('%d/%m/%Y') if student.date_of_admission else '',
                'programme': programme,
                '+2_group': '',
                '+2class/distinction': '',
                '+2year': '',
                'degree_year': '',
                'degree_subject': '',
                'date_of_leaving': '',
                'tc_no': '',
            }
            lines.append(vals)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': lines,
        }
