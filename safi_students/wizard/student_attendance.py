from odoo import fields, models, api
from odoo.exceptions import Warning, UserError, ValidationError
import urllib


class StudentAttendanceWizard(models.TransientModel):
    _name = 'student.attendance.wizard'
    _description = 'Student Attendance Wizard'

    batch_id = fields.Many2one('batch.batch')
    semester_id = fields.Many2one('semester.semester')
    course_id = fields.Many2one('course.course')
    date = fields.Date(default=fields.Date.today())
    attendance_line_ids = fields.One2many('student.attendance.line.wizard', 'attendance_id')
    hour = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'),
         ('all_hours', 'All Hours')])
    user_id = fields.Many2one('res.users', 'Faculty', default=lambda self: self.env.uid)
    second_language_id = fields.Many2one('second.language')
    attendance_status = fields.Selection([('absent', 'Absent'), ('present', 'Present')], default='absent')
    check_all = fields.Boolean()
    
    @api.onchange('attendance_line_ids')
    def check_all_items(self):
        if self.attendance_line_ids:
            if False in self.attendance_line_ids.mapped('is_absent'):
                self.check_all = False
            else:
                self.check_all = True
            for each in self.attendance_line_ids:
                each.checking_bool = True
                
    @api.onchange('check_all')
    def check_uncheck_line_ids(self):
        if self.attendance_line_ids:
            for each in self.attendance_line_ids:
                if not each.checking_bool:
                    if self.check_all:
                        each.is_absent = True
                    if not self.check_all:
                        each.is_absent = False

    @api.onchange('batch_id', 'semester_id', 'hour', 'date', 'second_language_id', 'attendance_status')
    def onchange_batch_id(self):
        self.attendance_line_ids = False
        new_lines = self.env['student.attendance.line.wizard']
        student_domain = [('batch_id', '=', self.batch_id.id)]
        if self.second_language_id:
            student_domain.append(('second_language_id', '=', self.second_language_id.id))
        if self.batch_id and self.date and self.semester_id and self.hour:
            students = self.env['student.student'].search(student_domain, order='name ASC')
            for student in students:
                domain = [('student_id', '=', student.id), ('semester_id', '=', self.semester_id.id),
                          ('date', '=', self.date)]
                values = {
                    'student_id': student.id,
                    'admission_number': student.admission_number,
                    'roll_no': student.roll_no,
                }
                student_attendance = self.env['student.attendance'].search(domain)
                if self.attendance_status == 'absent':
                    if self.hour == '1' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_1 == 'A' else False})
                    if self.hour == '2' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_2 == 'A' else False})
                    if self.hour == '3' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_3 == 'A' else False})
                    if self.hour == '4' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_4 == 'A' else False})
                    if self.hour == '5' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_5 == 'A' else False})
                    if self.hour == '6' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_6 == 'A' else False})
                    if self.hour == '7' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_7 == 'A' else False})
                    if self.hour == '8' or self.hour == 'all_hours':
                        values.update({'is_absent': True if student_attendance.hour_8 == 'A' else False})
                else:
                    if self.hour == '1' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_1 == 'A' else True})
                    if self.hour == '2' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_2 == 'A' else True})
                    if self.hour == '3' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_3 == 'A' else True})
                    if self.hour == '4' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_4 == 'A' else True})
                    if self.hour == '5' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_5 == 'A' else True})
                    if self.hour == '6' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_6 == 'A' else True})
                    if self.hour == '7' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_7 == 'A' else True})
                    if self.hour == '8' or self.hour == 'all_hours':
                        values.update({'is_absent': False if student_attendance.hour_8 == 'A' else True})
                # if student.id == 26:
                #     raise UserError(str(values))
                new_line = new_lines.new(values)
                new_lines += new_line
            self.attendance_line_ids += new_lines
        if self.batch_id and self.semester_id:
            course = self.env['curriculum.curriculum'].search(
                [('programme_ids', 'in', self.batch_id.programme_id.ids),
                 ('semester_id', '=', self.semester_id.id)]).mapped('course_ids')
            # course = self.env['curriculum.line'].search([('curriculum_id.batch_id', '=', self.batch_id.id), (
            #     'curriculum_id.semester_id', '=', self.semester_id.id)]).mapped('course_id')
            return {'domain': {'course_id': [('id', 'in', course.ids)]}}
        else:
            return {'domain': {'course_id': [('id', 'in', [])]}}

    @api.model
    def create(self, values):
        res = super(StudentAttendanceWizard, self).create(values)
        res.mark_attendance()
        return res

    def write(self, values):
        self.mark_attendance()
        return super(StudentAttendanceWizard, self).write(values)

    def mark_attendance(self):
        for each in self.attendance_line_ids:
            values = {}
            domain = [('student_id', '=', each.student_id.id), ('semester_id', '=', self.semester_id.id),
                      ('date', '=', self.date)]
            course = self.course_id.id if self.course_id else False
            if self.attendance_status == 'absent':
                if self.hour == '1' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_1': 'A', 'course_id_1': self.course_id.id, 'user_id_1': self.user_id.id})
                    else:
                        values.update({'hour_1': 'X', 'course_id_1': self.course_id.id, 'user_id_1': self.user_id.id})
                if self.hour == '2' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_2': 'A', 'course_id_2': self.course_id.id, 'user_id_2': self.user_id.id})
                    else:
                        values.update({'hour_2': 'X', 'course_id_2': self.course_id.id, 'user_id_2': self.user_id.id})
                if self.hour == '3' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_3': 'A', 'course_id_3': self.course_id.id, 'user_id_3': self.user_id.id})
                    else:
                        values.update({'hour_3': 'X', 'course_id_3': self.course_id.id, 'user_id_3': self.user_id.id})
                if self.hour == '4' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_4': 'A', 'course_id_4': self.course_id.id, 'user_id_4': self.user_id.id})
                    else:
                        values.update({'hour_4': 'X', 'course_id_4': self.course_id.id, 'user_id_4': self.user_id.id})
                if self.hour == '5' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_5': 'A', 'course_id_5': self.course_id.id, 'user_id_5': self.user_id.id})
                    else:
                        values.update({'hour_5': 'X', 'course_id_5': self.course_id.id, 'user_id_5': self.user_id.id})
                if self.hour == '6' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_6': 'A', 'course_id_6': self.course_id.id, 'user_id_6': self.user_id.id})
                    else:
                        values.update({'hour_6': 'X', 'course_id_6': self.course_id.id, 'user_id_6': self.user_id.id})
                if self.hour == '7' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_7': 'A', 'course_id_7': self.course_id.id, 'user_id_7': self.user_id.id})
                    else:
                        values.update({'hour_7': 'X', 'course_id_7': self.course_id.id, 'user_id_7': self.user_id.id})
                if self.hour == '8' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_8': 'A', 'course_id_8': self.course_id.id, 'user_id_8': self.user_id.id})
                    else:
                        values.update({'hour_8': 'X', 'course_id_8': self.course_id.id, 'user_id_8': self.user_id.id})
            else:
                if self.hour == '1' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_1': 'X', 'course_id_1': self.course_id.id, 'user_id_1': self.user_id.id})
                    else:
                        values.update({'hour_1': 'A', 'course_id_1': self.course_id.id, 'user_id_1': self.user_id.id})
                if self.hour == '2' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_2': 'X', 'course_id_2': self.course_id.id, 'user_id_2': self.user_id.id})
                    else:
                        values.update({'hour_2': 'A', 'course_id_2': self.course_id.id, 'user_id_2': self.user_id.id})
                if self.hour == '3' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_3': 'X', 'course_id_3': self.course_id.id, 'user_id_3': self.user_id.id})
                    else:
                        values.update({'hour_3': 'A', 'course_id_3': self.course_id.id, 'user_id_3': self.user_id.id})
                if self.hour == '4' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_4': 'X', 'course_id_4': self.course_id.id, 'user_id_4': self.user_id.id})
                    else:
                        values.update({'hour_4': 'A', 'course_id_4': self.course_id.id, 'user_id_4': self.user_id.id})
                if self.hour == '5' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_5': 'X', 'course_id_5': self.course_id.id, 'user_id_5': self.user_id.id})
                    else:
                        values.update({'hour_5': 'A', 'course_id_5': self.course_id.id, 'user_id_5': self.user_id.id})
                if self.hour == '6' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_6': 'X', 'course_id_6': self.course_id.id, 'user_id_6': self.user_id.id})
                    else:
                        values.update({'hour_6': 'A', 'course_id_6': self.course_id.id, 'user_id_6': self.user_id.id})
                if self.hour == '7' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_7': 'X', 'course_id_7': self.course_id.id, 'user_id_7': self.user_id.id})
                    else:
                        values.update({'hour_7': 'A', 'course_id_7': self.course_id.id, 'user_id_7': self.user_id.id})
                if self.hour == '8' or self.hour == 'all_hours':
                    if each.is_absent:
                        values.update({'hour_8': 'X', 'course_id_8': self.course_id.id, 'user_id_8': self.user_id.id})
                    else:
                        values.update({'hour_8': 'A', 'course_id_8': self.course_id.id, 'user_id_8': self.user_id.id})
            student_attendance = self.env['student.attendance'].search(domain)
            if student_attendance:
                student_attendance.write(values)                            
            else:
                values.update({
                    'student_id': each.student_id.id,
                    'semester_id': self.semester_id.id,
                    'date': self.date,
                })
                self.env['student.attendance'].create(values)
                
    def send_message(self):
        user_name = 'alfarook'    
        password = 'ALFEC@SMS'
        absentee_list = []
        if self.attendance_status == 'absent':
            for each in self.attendance_line_ids:
                if each.is_absent:
                    message = 'താങ്കളുടെ മകൻ/മകൾ %s ഇന്ന് ക്ലാസിൽ ഹാജരായിട്ടില്ല - അൽഫാറൂഖ്' % each.student_id.name
                    absentee_list.append(each.student_id.roll_no)
                    parameter = urllib.parse.urlencode({'username': user_name, 'password': password, 'mobile' : each.student_id.parent_mobile.replace(' ', ''), 
                                        'message': message, 'sendername': 'ALFCLT', 'UC': 'U', 'routetype': '1', 'tid': '1207166417445783835'})
                    url = "http://sapteleservices.com/SMS_API/sendsms.php?%s" % parameter
                    urllib.request.urlopen(url)
                    k = 1
        else:
            for each in self.attendance_line_ids:
                if each.is_absent == False:
                    message = 'താങ്കളുടെ മകൻ/മകൾ %s ഇന്ന് ക്ലാസിൽ ഹാജരായിട്ടില്ല - അൽഫാറൂഖ്' % each.student_id.name
                    absentee_list.append(each.student_id.roll_no)
                    parameter = urllib.parse.urlencode({'username': user_name, 'password': password, 'mobile' : each.student_id.parent_mobile.replace(' ', ''), 
                                        'message': message, 'sendername': 'ALFCLT', 'UC': 'U', 'routetype': '1', 'tid': '1207166417445783835'})
                    url = "http://sapteleservices.com/SMS_API/sendsms.php?%s" % parameter
                    urllib.request.urlopen(url)
        # if len(absentee_list) > 0:
        #     teacher = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
        #     teacher_message = 'Today’s absentees Roll NO: %s.Alfarook' % ','.join(absentee_list)   
        #     teacher_parameter = urllib.parse.urlencode({'username': user_name, 'password': password, 'mobile' : teacher.mobile_phone.replace(' ', ''), 
        #                                     'message': teacher_message, 'sendername': 'ALFCLT', 'UC': 'U', 'routetype': '1', 'tid': '1207166417452198839'})
        #     teacher_url = "http://sapteleservices.com/SMS_API/sendsms.php?%s" % teacher_parameter   
        #     urllib.request.urlopen(teacher_url)            


class StudentAttendanceLineWizard(models.TransientModel):
    _name = 'student.attendance.line.wizard'
    _description = 'Student Attendance Line Wizard'

    student_id = fields.Many2one('student.student')
    attendance_id = fields.Many2one('student.attendance.wizard')
    roll_no = fields.Integer()
    admission_number = fields.Integer()
    is_absent = fields.Boolean()
    checking_bool = fields.Boolean(default=False)
    
    
class MessageAbsentees(models.TransientModel):
    _name = 'message.absentees'
    _description = 'Message Absentees'
    
    date = fields.Date()
    
    def message_absentees(self):
        user_name = 'alfarook'    
        password = 'ALFEC@SMS'
        attendances = self.env['student.attendance'].search([('date', '=', self.date)])
        for attendance in attendances:
            hour_status = []
            if attendance.hour_1 == 'A':
                hour_status.append('A')
            if attendance.hour_2 == 'A':
                hour_status.append('A')
            if attendance.hour_3 == 'A':
                hour_status.append('A')
            if attendance.hour_4 == 'A':
                hour_status.append('A')
            if attendance.hour_5 == 'A':
                hour_status.append('A')
            if attendance.hour_6 == 'A':
                hour_status.append('A')
            if attendance.hour_7 == 'A':
                hour_status.append('A')
            if attendance.hour_8 == 'A':
                hour_status.append('A')
            if 'A' in hour_status:
                url = "http://sapteleservices.com/SMS_API/sendsms.php?username=%s&password=%s&mobile=9633778355&message=താങ്കളുടെ മകൻ/മകൾ ഇന്ന് ക്ലാസിൽ ഹാജരായിട്ടില്ല - അൽഫാറൂഖ്&sendername=ALFCLT&UC=U&routetype=1&tid=1207166021714149139" % (user_name, password)
                parameter = urllib.parse.urlencode({'username': user_name, 'password': password, 'mobile' : attendance.student_id.parent_mobile.replace(' ', ''), 
                                    'message': 'താങ്കളുടെ മകൻ/മകൾ ഇന്ന് ക്ലാസിൽ ഹാജരായിട്ടില്ല - അൽഫാറൂഖ്', 
                                    'sendername': 'ALFCLT', 'UC': 'U', 'routetype': '1', 'tid': '1207166021714149139'})
                url = "http://sapteleservices.com/SMS_API/sendsms.php?%s" % parameter
                urllib.request.urlopen(url) 
