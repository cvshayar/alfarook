from odoo import fields, models, api


class BatchFeeLoad(models.TransientModel):
    _name = 'batch.fee.load'

    def get_acdemic_year(self):
        if fields.Date.today().strftime('%B') in ['January', 'February', 'March', 'April', 'May']:
            academic_year = fields.Date.today().year - 1
        else:
            academic_year = fields.Date.today().year
        return academic_year

    batch_ids = fields.Many2many('batch.batch')
    batch_year = fields.Integer()
    semester_id = fields.Many2one('semester.semester')
    academic_year = fields.Integer(default=get_acdemic_year)
    fee_category_ids = fields.Many2many('fee.category')

    # installment_id = fields.Many2one('fee.installment')

    @api.onchange('batch_ids')
    def onchange_batch_ids(self):
        if self.batch_year:
            self.semester_id = self.batch_ids[0].current_semester_id.id

    def loading_batch_fee(self):
        # if self.semester_id.name in ['1', '2']:
        #     academic_year = self.batch_id.start_year
        # elif self.semester_id.name in ['3', '4']:
        #     academic_year = self.batch_id.start_year - 1
        # else:
        #     academic_year = self.batch_id.start_year - 2
        for batch in self.batch_ids:
            programme_fee = self.env['programme.fee'].search(
                [('programme_ids', 'in', batch.programme_id.ids), ('fee_category_ids', 'in', self.fee_category_ids.ids),
                 ('academic_year', '=', self.academic_year), ('semester_id', '=', self.semester_id.id)])
            students = self.env['student.student'].search([('batch_id', '=', batch.id)])
            for student in students:
                for each in programme_fee.programme_line:
                    student_fee = self.env['student.fee.dues'].search(
                        [('academic_year', '=', self.academic_year), ('student_id', '=', student.id),
                         ('fee_id', '=', each.fee_id.id), ('semester_id', '=', self.semester_id.id)])
                    if student_fee:
                        student_fee.write({'gross_payable_amount': each.amount})
                        student_fee.calculate_net_payable_amount()
                    else:
                        values = {
                            'academic_year': self.academic_year,
                            'student_id': student.id,
                            'fee_id': each.fee_id.id,
                            'gross_payable_amount': each.amount,
                            'net_payable_amount': each.amount,
                            'semester_id': self.semester_id.id,
                            # 'installment_id': each.programme_fee_id.installment_id.id
                        }
                        fee = self.env['student.fee.dues'].create(values)
                        fee.calculate_net_payable_amount()
