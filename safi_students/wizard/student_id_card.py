from odoo import fields, models, api


class StudentIDCardWizard(models.TransientModel):
    _name = 'student.idcard.wizard'
    _description = 'Student ID Card'

    year = fields.Selection(
        [(str(num), str(num)) for num in range(fields.Date.today().year - 10, fields.Date.today().year + 1)],
        default=str(fields.Date.today().year), string='Year')
    batch_id = fields.Many2one('batch.batch')
    student_ids = fields.Many2many('student.student')
    print = fields.Selection([('front', 'Front'), ('back', 'Back')], default='front')

    def print_id_card(self):
        student_list = []
        for each in self.student_ids:
            student_list.append(str(each.admission_number))
        students = ','.join(student_list)
        return {
            'type': 'ir.actions.act_url',
            'url': 'student/id_card/%s/%s' % (students, self.print),
            'target': 'new'
        }

