# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, exceptions, _
from odoo.osv import expression


class FeePendingReport(models.TransientModel):
    _name = "fee.pending.list"
    _description = 'Fee Pending Report'

    student_id = fields.Many2one('student.student', string="Student")
    academic_year = fields.Integer(default=fields.Date.today().year)
    semester_id = fields.Many2one('semester.semester')
    batch_id = fields.Many2one('batch.batch')
    fee_id = fields.Many2one('fees.item')

    def return_fee_due_view(self):
        self.ensure_one()
        domain = [('balance', '>', 0), ('student_id.tc_issued', '=', False), ('student_id', '!=', False)]
        if self.student_id:
            domain.append(('student_id', '=', self.student_id.id))
        if self.academic_year:
            domain.append(('academic_year', '=', self.academic_year))
        if self.batch_id:
            domain.append(('batch_id', '=', self.batch_id.id))
        if self.semester_id:
            domain.append(('semester_id', '=', self.semester_id.id))
        if self.fee_id:
            domain.append(('fee_id', '=', self.fee_id.id))
        return {
            'name': _('Due Report'),
            'domain': domain,
            'res_model': 'student.fee.dues',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                               
                                            </p>'''),
            'limit': 80,
            'context': {'create': False, 'delete': False}
        }


