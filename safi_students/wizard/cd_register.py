import pytz
from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError


class CDRegisterWizard(models.TransientModel):
    _name = 'cd.register.wizard'

    programme_type = fields.Selection([('aided', 'Aided'), ('self_finance', 'Self Finance')], default='self_finance')
    year = fields.Integer(default=fields.Date.today().year)

    def generate_report(self):
        data = {'model_id': self.id, 'programme_type': self.programme_type, 'year': self.year}
        return self.env.ref('safi_students.cd_register_report_pdf_id').report_action(self, data=data, config=False)


class CDRegisterPdf(models.Model):
    _name = 'report.safi_students.cd_register_report_pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        lines = []
        domain = ['|', ('active', '=', True), ('active', '=', False),
                  ('fee_category_id.name', 'not in', ['SC', 'ST', 'OEC']), ('admission_number', '>', 0),
                  ('year_of_admission', '=', data['year'])]
        if data['programme_type'] == 'aided':
            domain.append(('self_finance', '=', False))
        else:
            domain.append(('self_finance', '=', True))
        students = self.env['student.student'].search(domain, order='admission_number ASC')
        for each in students:
            fees = self.env['fee.collection'].search([('student_id', '=', each.id), ('state', '=', 'paid')])
            cd = [sum(fee.fee_line.filtered(lambda x: x.fee_id.name == 'CD').mapped('amount')) for fee in fees]
            fee_dates = self.env['fee.collection.line'].search(
                [('fee_id.name', '=', 'CD'), ('fee_collection_id.student_id', '=', each.id)]).mapped(
                'fee_collection_id')
            vals = {
                'student': each,
                'cd': cd,
                'date': [fee_date.payment_date.strftime('%d/%m/%Y') for fee_date in fee_dates]
            }
            lines.append(vals)

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': lines,
        }
