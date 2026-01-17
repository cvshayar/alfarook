from odoo import fields, models, api
from odoo.exceptions import Warning, UserError


class Course(models.Model):
    _name = 'course.course'
    _description = 'Course'
    _rec_name = 'complete_name'

    name = fields.Char('Title')
    code = fields.Char()
    complete_name = fields.Char(compute='compute_name')

    @api.depends('name', 'code')
    def compute_name(self):
        for each in self:
            each.complete_name = ''
            if each.name and each.code:
                each.complete_name = each.code + ' ' + each.name

    def unlink(self):
        for each in self:
            curriculum_course = self.env['curriculum.line'].search([('course_id', '=', each.id)])
            if len(curriculum_course) > 0:
                raise UserError(str('You are not allowed to delete course'))
            return super(Course, self).unlink()


class Curriculum(models.Model):
    _name = 'curriculum.curriculum'
    _description = 'Curriculum'

    name = fields.Char(compute='compute_name')
    # batch_id = fields.Many2one('batch.batch')
    programme_ids = fields.Many2many('programme.programme')
    year = fields.Integer(default=fields.Date.today().year, string='Start Year')
    course_ids = fields.Many2many('course.course')
    semester_id = fields.Many2one('semester.semester')
    # curriculum_line_ids = fields.One2many('curriculum.line', 'curriculum_id')

    @api.depends('programme_ids', 'semester_id')
    def compute_name(self):
        for each in self:
            each.name = ''
            if each.semester_id and each.programme_ids:
                each.name = each.semester_id.name + ' ' + ' '.join(each.programme_ids.mapped('name'))


# class CurriculumLine(models.Model):
#     _name = 'curriculum.line'
#     _description = 'CurriculumLine'
#
#     course_id = fields.Many2one('course.course')
#     curriculum_id = fields.Many2one('curriculum.curriculum')
#     display_index = fields.Integer()


class StudentAttendance(models.Model):
    _name = 'student.attendance'
    _description = 'StudentAttendance'

    student_id = fields.Many2one('student.student')
    semester_id = fields.Many2one('semester.semester')
    date = fields.Date()
    hour_1 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    hour_2 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    hour_3 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    hour_4 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    hour_5 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    hour_6 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    hour_7 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    hour_8 = fields.Selection([('X', 'X'), ('A', 'A'), ('N', 'N')], default='N')
    course_id_1 = fields.Many2one('course.course')
    course_id_2 = fields.Many2one('course.course')
    course_id_3 = fields.Many2one('course.course')
    course_id_4 = fields.Many2one('course.course')
    course_id_5 = fields.Many2one('course.course')
    course_id_6 = fields.Many2one('course.course')
    course_id_7 = fields.Many2one('course.course')
    course_id_8 = fields.Many2one('course.course')
    user_id_1 = fields.Many2one('res.users')
    user_id_2 = fields.Many2one('res.users')
    user_id_3 = fields.Many2one('res.users')
    user_id_4 = fields.Many2one('res.users')
    user_id_5 = fields.Many2one('res.users')
    user_id_6 = fields.Many2one('res.users')
    user_id_7 = fields.Many2one('res.users')
    user_id_8 = fields.Many2one('res.users')
