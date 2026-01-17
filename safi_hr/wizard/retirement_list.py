from odoo import fields, models, api
from datetime import datetime, date, timedelta


class RetiredList(models.TransientModel):
    _name = 'retired.list.report'
    _description = 'Description'

    year = fields.Selection(
        [(str(num), str(num)) for num in range(datetime.now().year - 10, datetime.now().year + 11)],
        default=datetime.now().year, string='Year', required=True)

    def generate_report(self):
        data = {'model_id': self.id, 'year': int(self.year)}
        return self.env.ref('safi_hr.retired_list_pdf_id').report_action(self, data=data)


class AdmissionRegisterPdf(models.Model):
    _name = 'report.safi_hr.retired_list_pdf'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        from_date = '01-01-%d' % data['year']
        from_date = datetime.strptime(from_date, '%d-%m-%Y').date()
        to_date = '31-12-%d' % data['year']
        to_date = datetime.strptime(to_date, '%d-%m-%Y').date()
        domain = ['|', ('active', '=', True), ('active', '=', False), ('retirement_date', '>=', from_date),
                  ('retirement_date', '<=', to_date)]
        employees = self.env['hr.employee'].search(domain, order='retirement_date ASC')
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': employees,
        }


