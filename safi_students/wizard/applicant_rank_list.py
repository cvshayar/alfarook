from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
from odoo import http
import urllib
import ast, json


class ApplicantRankList(models.TransientModel):
    _name = 'applicant.rank.list'

    programme_id = fields.Many2one('programme.programme')
    category = fields.Selection([('ETB', 'Ezhava, Thiyya & Billava (ETB)'), ('GEN', 'General (GEN)'), ('Muslim', 'Muslim'),
                                 ('EWS', 'General-Economically Weaker Sections (EWS)'), ('LC', 'Latin Catholics other than Anglo Indians (LC)'),
                                 ('OBH', 'Other Backward Hindus (OBH)'), ('OBX', 'Other Backward Christians (OBX)'),
                                 ('SC', 'SC'), ('ST', 'ST')])
    lock_status = fields.Selection([('1', 'Locked'), ('0', 'Not Locked'), ('-1', 'Both')], default='1')
    preference = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')])

    def generate_report(self):
        data = {'model_id': self.id, 'programme_id': self.programme_id.code, 'lock_status': self.lock_status, 'category': self.category, 'preference': self.preference}
        return self.env.ref('safi_students.applicant_rank_list_pdf_id').report_action(self, data=data)


# PDF
class ApplicantRankListPdf(models.Model):
    _name = 'report.safi_students.applicant_rank_list_pdf'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        lines = []
        application_api_url = http.request.env['ir.config_parameter'].sudo().get_param('application_api_url')
        url = '%s/api/api.php?r=_ugapplist&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09&lk=%s&ct=%s&co=%s' % (
            application_api_url, data['lock_status'], data['category'], data['programme_id'])
        val = urllib.request.urlopen(url).read(1000000).decode("utf-8")
        val = json.loads(val)
        val = ast.literal_eval("%s" % val)
        if data['preference']:
            val = [d for d in val if d['pref'] == data['preference']]
        # raise UserError(val)
        # for each in val:
        #     values = {
        #         'application_number': each['controlno'],
        #         'name': each['applname'],
        #         'category': each['category'],
        #         'programme': self.env['programme.programme'].search([('code', '=', each['courseopted'])]).name,
        #         'preference': each['pref'],
        #         'percentage': each['percentage']
        #     }
        #     lines.append(values)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'lines': val,
        }