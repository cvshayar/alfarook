from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError


class AdmissionSummaryWizard(models.TransientModel):
    _name = 'admission.summary.wizard'

    @api.model
    def _get_default_start_year(self):
        return str(fields.Date.today().year)

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(num), str(num)) for num in range(current_year - 8, current_year + 1)]

    batch_year = fields.Selection(
        selection=_get_year_selection, 
        default=_get_default_start_year, 
        string='Batch Year'
    )
    from_date = fields.Date(default=fields.Date.today())
    to_date = fields.Date(default=fields.Date.today())
    batch_ids = fields.Many2many('batch.batch')
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG')])
    report_form = fields.Selection([('Count', 'Count'), ('Detailed Admitted', 'Detailed Admission Report')])
    report_type = fields.Selection(
        [('religion', 'Religion'), ('caste', 'Caste'), ('second_language', 'Second Language'),
         ('admission_category', 'Admission Category'), ('category', 'Caste Category'),
         ('fee_category', 'Fee Category')])
    detailed_report_type = fields.Selection(
        [('religion', 'Religion'), ('caste', 'Caste'), ('second_language', 'Second Language'),
         ('admission_category', 'Admission Category'), ('category', 'Caste Category'),
         ('fee_category', 'Fee Category')])
    field_select_ids = fields.Many2many('ir.model.fields')
    fee_status = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Include Fee Status')
    religion_ids = fields.Many2many('religion.religion')
    caste_ids = fields.Many2many('caste.caste')
    caste_category_ids = fields.Many2many('caste.category')
    admission_category_ids = fields.Many2many('admission.category')
    fee_category_ids = fields.Many2many('fee.category')
    second_language_ids = fields.Many2many('second.language')
    sort_order = fields.Selection(
        [('religion', 'Religion'), ('caste', 'Caste'), ('second_language', 'Second Language'),
         ('admission_category', 'Admission Category'), ('category', 'Caste Category'),
         ('fee_category', 'Fee Category'), ('index', 'index')])

    def print_excel_report(self):
        admission_domain = ['|', ('active', '=', False), ('active', '=', True), ('admission_number', '>', 0)]
        not_admission_domain = ['|', ('active', '=', False), ('active', '=', True), ('admission_number', '=', 0)]
        if self.from_date:
            admission_domain.append(('date_of_admission', '>=', self.from_date))
            not_admission_domain.append(('date_of_admission', '>=', self.from_date))
        if self.to_date:
            admission_domain.append(('date_of_admission', '<=', self.to_date))
            not_admission_domain.append(('date_of_admission', '<=', self.to_date))
        if self.batch_ids:
            batches = self.env['batch.batch'].browse(self.batch_ids.ids)
            admission_domain.append(('batch_id', 'in', batches.ids))
            not_admission_domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', self.batch_year)])
            admission_domain.append(('batch_id', 'in', batches.ids))
            not_admission_domain.append(('batch_id', 'in', batches.ids))
        if not self.env['student.student'].search(admission_domain):
            raise UserError(str('No Admission'))
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'admission.summary.report', 'form': self.read()[0]}
        if self.report_form == 'Detailed Admitted':
            return self.env.ref('safi_students.detailed_admission_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                                       config=False)
        if self.report_form == 'Count' and self.report_type == 'religion':
            return self.env.ref('safi_students.religion_admission_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                                       config=False)
        if self.report_form == 'Count' and self.report_type == 'caste':
            return self.env.ref('safi_students.caste_admission_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                                    config=False)
        if self.report_form == 'Count' and self.report_type == 'category':
            return self.env.ref('safi_students.category_admission_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                                       config=False)
        if self.report_form == 'Count' and self.report_type == 'second_language':
            return self.env.ref('safi_students.language_admission_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                                       config=False)
        if self.report_form == 'Count' and self.report_type == 'admission_category':
            return self.env.ref('safi_students.admission_category_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                                       config=False)
        if self.report_form == 'Count' and self.report_type == 'fee_category':
            return self.env.ref('safi_students.fee_admission_summary_report_xlsx_id').report_action(self, data=datas,
                                                                                                  config=False)
