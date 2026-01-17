from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning, UserError
import pytz
import urllib.request
import ast, json
from odoo import http


class TcApplication(models.Model):
    _name = 'tc.applications'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'tc_application_no'
    _order = 'tc_application_no DESC'

    tc_application_no = fields.Integer()
    admission_number = fields.Integer()
    student_name = fields.Char('Name of  the student')
    dob = fields.Date('Date of birth')
    admission_year = fields.Char()
    admission_date = fields.Date('Date of Admission')
    date_of_leave = fields.Date('The last date he/she attended college')
    programme_admitted_id = fields.Many2one('programme.programme', 'Programme in which the student admitted')
    semester_admitted = fields.Char()
    programme_id = fields.Many2one('programme.programme', 'Programme in which the student studied')
    semester = fields.Char('Semester in which the student admitted')
    reason = fields.Char('Reason for Transfer Certificate')
    promotion = fields.Char('Qualified for promotion')
    exam_semester = fields.Char('Semester of Examination last appeared from the college')
    exam_year = fields.Char('Year of examination last appeared from the college')
    exam_register_number = fields.Char('Register no. of examination')
    exam_passed = fields.Char()
    date_of_application = fields.Date()
    is_approved = fields.Boolean()
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('issued', 'Issued')], default='draft',
                             track_visibility='onchange')
    tc_clearance_id = fields.Many2one('tc.clearance')
    due_status = fields.Selection([('Dues', 'Dues'), ('No Dues', 'No Dues')], compute='get_due_status')

    @api.depends('tc_clearance_id.clearance_line')
    def get_due_status(self):
        for each in self:
            # if each.tc_application_no == 413:
            #     raise UserError(str(each.tc_clearance_id.clearance_line.mapped('dues')))
            if int(len(each.tc_clearance_id.clearance_line)) == int(len(
                    each.tc_clearance_id.clearance_line.mapped('dues'))) and int(len(
                each.tc_clearance_id.clearance_line)) > 0:
                if 'Dues' in each.tc_clearance_id.clearance_line.mapped('dues'):
                    each.due_status = 'Dues'
                elif False in each.tc_clearance_id.clearance_line.mapped('dues'):
                    each.due_status = 'Dues'
                else:
                    each.due_status = 'No Dues'
            else:
                each.due_status = 'Dues'

    def approve_application(self):
        tc_application = self.env['tc.applications'].search(
            [('admission_number', '=', self.admission_number), ('state', 'in', ['approved', 'issued'])])
        tc = self.env['tc.issued.register'].search(
            [('admission_number', '=', self.admission_number), ('state', '=', 'issue')])
        if tc_application:
            raise UserError(str("Application is already approved"))
        if tc:
            raise UserError(str("TC already issued"))

        self.write({'state': 'approved'})

    def unlink(self):
        for tc in self:
            if tc.state == 'approved':
                raise UserError(str("You don't have the permission to delete TC Application"))
        return super(TcApplication, self).unlink()

    def issue_tc(self):
        tc_form = self.env.ref('safi_students.tc_to_issue_form', False)
        return {
            'name': _('Issue TC'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tc.issued.register',
            'views': [(tc_form.id, 'form')],
            'view_id': tc_form.id,
            'target': 'new',
            'context': {'default_admission_number': self.admission_number, 'default_app_ref': self.tc_application_no},
        }

    def tc_clearance(self):
        tc_form = self.env.ref('safi_students.tc_clearance_form', False)
        if not self.tc_clearance_id:
            return {
                'name': _('TC Clearance'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'tc.clearance',
                'views': [(tc_form.id, 'form')],
                'view_id': tc_form.id,
                'target': 'new',
                'context': {'default_application_id': self.id},
            }
        else:
            return {
                'name': _('TC Clearance'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'tc.clearance',
                'res_id': self.tc_clearance_id.id,
                'views': [(tc_form.id, 'form')],
                'view_id': tc_form.id,
                'target': 'new',
                'context': {'default_application_id': self.id},
            }

    def print_application(self):
        attendance_api_url = http.request.env['ir.config_parameter'].sudo().get_param('attendance_api_url')
        return {
            'type': 'ir.actions.act_url',
            'url': '%s/tc/tcapplicationpdf.php?ad=%s' % (attendance_api_url, self.admission_number),
            'target': 'new',
            # 'res_id': self.id,
        }


class TcRegister(models.Model):
    _name = 'tc.issued.register'
    _order = 'tc_academic_year DESC, name DESC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Integer('TC Number', readonly=True)
    tc_register_sequence = fields.Integer()
    is_visible = fields.Boolean(default=False)
    student_id = fields.Many2one('student.student', 'Name of student ')
    student_name = fields.Char('Name of student')
    admission_number = fields.Integer(track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('issue', 'TC Issue'), ('cancelled', 'Cancelled')],
        default='draft', track_visibility='onchange')
    dob = fields.Date('Date of birth')
    date_of_admission = fields.Date('Date of admission')
    admission_year = fields.Selection([(str(num), str(num)) for num in range(fields.Datetime.now().year + 1, 1990, -1)])
    date_of_leave = fields.Date('Date of leaving')
    programme_id = fields.Many2one('programme.programme', 'Programme in which the student studied',
                                   track_visibility='onchange')
    semester_id = fields.Many2one('semester.semester', 'Semester in which the student studied')
    promotion = fields.Selection(
        [('Programme Completed', 'Programme Completed'), ('Discontinued', 'Discontinued'), ('No', 'No'), ('Yes', 'Yes'),
         ('Transferred to Aided', 'Transferred to Aided'), ('Transferred to Self', 'Transferred to Self'),
         ('Discontinued/Transfer', 'Discontinued/Transfer')],
        string='Qualified for promotion')
    dues = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Student has paid all fee dues")
    exam_semester_id = fields.Many2one('semester.semester', string='Semester of Examination last appeared from the college')
    exam_year = fields.Selection([(str(num), str(num)) for num in range(fields.Datetime.now().year + 1, 1990, -1)],
                                 string='Year of examination last appeared from the college')
    exam_reg_no = fields.Char('Register no. of examination')
    ex_passed = fields.Selection(
        [('Passed', 'Passed'), ('Result awaiting', 'Result Awaiting'), ('Discontinued', 'Discontinued'),
         ('Refer the Marklist', 'Refer the Marklist'), ('Failed', 'Failed'), ('Transferred', 'Transferred')],
        string='Whether passed or failed')
    tc_applied_date = fields.Date(string='Date of application for TC')
    tc_issued_date = fields.Date(required=True, default=fields.Date.today, string='Date of TC')
    is_self_finance = fields.Boolean(default=False)
    conduct = fields.Selection([('good', 'Good'), ('satisfactory', 'Satisfactory')], string='Conduct during the period')
    tc_academic_year = fields.Integer()
    app_ref = fields.Integer()
    is_transfer = fields.Boolean()
    batch_id = fields.Many2one('batch.batch', related='student_id.batch_id', store=True)

    @api.model
    def create(self, values):
        tc_application = self.env['tc.applications'].search([('admission_number', '=', values['admission_number'])])
        tc_register = self.env['tc.issued.register'].search([('admission_number', '=', values['admission_number'])],
                                                            limit=1)
        if tc_register:
            raise UserError(str('TC already issued with TC Number %s' % tc_register.name))
        if not values['is_transfer']:
            if tc_application:
                if tc_application.state == 'draft':
                    raise UserError(
                        str('TC Application with number %s is not approved' % tc_application.tc_application_no))
            else:
                raise UserError(str('No TC Application'))
        domain = [('tc_academic_year', '=', values['tc_academic_year'])]
        if values['is_self_finance']:
            domain.append(('is_self_finance', '=', True))
        else:
            domain.append(('is_self_finance', '=', False))
        tc_register = self.env['tc.issued.register'].search(domain, order='name DESC', limit=1)
        values['name'] = tc_register.name + 1
        values['state'] = 'issue'
        if values['exam_reg_no']:
            values['exam_reg_no'] = values['exam_reg_no'].upper()
        student = self.env['student.student'].search(
            ['|', ('active', '=', False), ('active', '=', True), ('admission_number', '=', values['admission_number'])])
        if not values['is_transfer']:
            if values['app_ref'] > 0:
                tc_app = self.env['tc.applications'].search([('tc_application_no', '=', values['app_ref'])])
                tc_clearance = self.env['tc.clearance'].search(
                    [('application_id.tc_application_no', '=', values['app_ref'])])
                tc_app.write({'state': 'issued'})
                tc_clearance.write({'state': 'issued'})
        student.write({'tc_issued': True, 'active': False})
        return super(TcRegister, self).create(values)

    @api.onchange('admission_number', 'student_id')
    def onchange_admission_number(self):
        if self.student_id:
            self.admission_number = self.student_id.admission_number
        if self.admission_number:
            student = self.env['student.student'].search(
                ['|', ('active', '=', False), ('active', '=', True), ('admission_number', '=', self.admission_number)])
            tc_application = self.env['tc.applications'].search([('admission_number', '=', self.admission_number)])
            tc_register = self.env['tc.issued.register'].search([('admission_number', '=', self.admission_number)],
                                                                limit=1)
            semester = self.env['semester.semester'].search([('name', '=', tc_application.semester)])
            exam_semester = self.env['semester.semester'].search([('name', '=', tc_application.exam_semester)])
            self.student_id = student.id
            self.programme_id = student.programme_id.id if student.programme_id else tc_application.programme_id.id
            self.date_of_admission = student.date_of_admission if student.date_of_admission else tc_application.admission_date if tc_application.admission_date != '-' else ''
            self.dob = student.dob if student.dob else tc_application.dob if tc_application.dob != '-' else ''
            self.semester_id = student.semester_id.id if student.semester_id else semester.id if semester else ''
            # self.exam_reg_no = student.reg_no if student.reg_no else tc_application.exam_register_number
            self.is_self_finance = student.programme_id.is_self_finance if student.programme_id else tc_application.programme_id.is_self_finance
            self.exam_reg_no = student.reg_no if student else tc_application.exam_register_number if tc_application.exam_register_number != '-' else ''
            self.exam_semester_id = exam_semester.id if exam_semester else ''
            self.tc_applied_date = tc_application.date_of_application
            self.admission_year = student.year_of_admission if student.year_of_admission else tc_application.admission_year if tc_application.admission_year != '-1' else ''
            self.exam_year = tc_application.exam_year if tc_application.exam_year != '-' else ''
            self.student_name = tc_application.student_name
            self.date_of_leave = tc_application.date_of_leave
            if tc_application.exam_passed == 'Refer to the Marklist':
                self.ex_passed = 'Refer the Marklist'
            else:
                self.ex_passed = tc_application.exam_passed if tc_application.exam_passed != '-' else ''
            self.app_ref = tc_application.tc_application_no
            # self.write({'student_name': tc_application.student_name})
            if not student:
                self.is_visible = True
            if tc_register:
                raise UserError(str('TC already issued with TC Number %s' % tc_register.name))
            if not self.is_transfer:
                if tc_application:
                    if tc_application.state == 'draft':
                        raise UserError(
                            str('TC Application with number %s is not approved' % tc_application.tc_application_no))
                else:
                    raise UserError(str('No TC Application'))

    @api.onchange('tc_issued_date')
    def onchange_tc_date(self):
        if self.tc_issued_date:
            if self.tc_issued_date.strftime('%B') in ['January', 'February', 'March', 'April', 'May']:
                self.tc_academic_year = self.tc_issued_date.year - 1
            else:
                self.tc_academic_year = self.tc_issued_date.year

    def confirm_tc(self):
        self.write({'state': 'confirm'})

    def unlink(self):
        for tc in self:
            if tc.state == 'cancelled':
                raise UserError(str('You dont have the permission to delete TC'))
        return super(TcRegister, self).unlink()

    def cancel_tc(self):
        self.write({'state': 'cancelled'})
        student = self.env['student.student'].search([('admission_number', '=', self.admission_number)])
        student.write({'tc_issued': False, 'active': True})
        tc_application = self.env['tc.applications'].search(
            [('admission_number', '=', self.admission_number), ('state', '=', 'issued')])
        if tc_application:
            tc_application.write({'state': 'approved'})

    def reset_to_draft(self):
        self.write({'state': 'draft'})

    def get_roman_value(self, num):
        return roman_numerals.convert(num)

    def issue_tc(self):
        domain = [('state', '=', 'issue')]
        if self.is_self_finance:
            domain.append(('is_self_finance', '=', True))
        else:
            domain.append(('is_self_finance', '=', False))
        tc_register = self.env['tc.issued.register'].search(domain, order='name DESC', limit=1)
        self.name = tc_register.name + 1
        self.write({'state': 'issue', 'tc_issued_date': fields.Date.today})
        student = self.env['student.student'].search([('admission_number', '=', self.admission_number)])
        student.write({'tc_issued': True})

    def update_student(self):
        tc = self.env['tc.issued.register'].search([])
        for each in tc:
            tc_application = self.env['tc.applications'].search(
                [('admission_number', '=', each.admission_number), ('state', '=', 'approved')])
            student = self.env['student.student'].search(
                ['|', ('active', '=', True), ('active', '=', False), ('admission_number', '=', each.admission_number)])
            each.write({'state': 'issue'})
            each.write({'student_id': student.id})
            each.write({'student_name': tc_application.student_name})
            if student:
                student.tc_issued = True
                student.active = False
            if not each.student_id:
                each.is_visible = True
                each.admission_year = tc_application.admission_year if tc_application.admission_year != '-1' else ''
            else:
                each.admission_year = each.student_id.yearofadmission

    def tc_applied_status(self):
        tc = self.env['tc.issued.register'].search([])
        for each in tc:
            tc_application = self.env['tc.applications'].search(
                [('admission_number', '=', each.admission_number), ('state', '=', 'approved')])
            if tc_application:
                tc_application.write({'state': 'issued'})


class TCClearance(models.Model):
    _name = 'tc.clearance'
    _description = 'TC Clearance'
    _rec_name = 'application_id'

    application_id = fields.Many2one('tc.applications')
    student_name = fields.Char(store=False, compute='get_image')
    programme_id = fields.Many2one('programme.programme', store=False, compute='get_image')
    admission_year = fields.Integer(store=False, compute='get_image')
    admission_number = fields.Integer(store=False, compute='get_image')
    application_number = fields.Integer(store=False, compute='get_image')
    image = fields.Binary(store=False, compute='get_image')
    clearance_line = fields.One2many('tc.clearance.line', 'clearance_id')
    section_ids = fields.Many2many('res.users', domain=lambda self: self.compute_user())
    state = fields.Selection([('draft', 'Draft'), ('issued', 'Issued')])

    @api.model
    def compute_user(self):
        user = self.env.user.id
        users = self.env.ref('safi_students.group_tc_clearance_user').users.ids
        domain = [('id', '!=', user), ('id', 'in', users)]
        return domain

    @api.depends('application_id')
    def get_image(self):
        for each in self:
            student = self.env['student.student'].search(
                ['|', ('active', '=', False), ('active', '=', True),
                 ('admission_number', '=', each.application_id.admission_number)])
            each.image = student.image
            each.student_name = each.application_id.student_name
            each.programme_id = each.application_id.programme_id
            each.admission_year = each.application_id.admission_year
            each.admission_number = each.application_id.admission_number
            each.application_number = each.application_id.tc_application_no

    def send_clearance(self):
        self.clearance_line = False
        new_lines = self.env['tc.clearance.line']
        for each in self.section_ids:
            data = {'section_id': each.id}
            new_line = new_lines.new(data)
            new_lines += new_line
        self.clearance_line += new_lines
        self.application_id.write({'tc_clearance_id': self.id})

    def resend_clearance(self):
        for each in self.section_ids:
            if not self.env['tc.clearance.line'].search(
                    [('section_id', '=', each.id), ('tc_clearance_id', '=', self.id)]):
                self.env['tc.clearance.line'].create({'section_id': each.id, 'tc_clearance_id': self.id})

    @api.model
    def create(self, values):
        values['state'] = 'draft'
        return super(TCClearance, self).create(values)


class TCClearanceLine(models.Model):
    _name = 'tc.clearance.line'
    _description = 'TC Clearance Line'
    _order = 'id DESC'

    clearance_id = fields.Many2one('tc.clearance')
    dues = fields.Selection([('Dues', 'Dues'), ('No Dues', 'No Dues')])
    remarks = fields.Text()
    section_id = fields.Many2one('res.users')
    student_name = fields.Char(store=False, compute='get_image')
    programme_id = fields.Many2one('programme.programme', store=True, compute='get_image')
    admission_year = fields.Integer(store=False, compute='get_image')
    roll_no = fields.Char(store=False, compute='get_image')
    admission_number = fields.Integer(store=False, compute='get_image')
    application_number = fields.Integer(store=False, compute='get_image')
    image = fields.Binary(store=False, compute='get_image')
    state = fields.Selection([('draft', 'Draft'), ('issued', 'Issued')], related='clearance_id.state', store=True)
    is_visible = fields.Boolean(compute='compute_visibility')

    @api.depends('is_visible')
    def compute_visibility(self):
        for each in self:
            if self.env.user.name == 'A4':
                each.is_visible = True
            else:
                each.is_visible = False

    @api.depends('clearance_id.application_id')
    def get_image(self):
        for each in self:
            student = self.env['student.student'].search(
                ['|', ('active', '=', False), ('active', '=', True),
                 ('admission_number', '=', each.clearance_id.application_id.admission_number)])
            each.image = student.image
            each.student_name = each.clearance_id.application_id.student_name
            each.programme_id = each.clearance_id.application_id.programme_id
            each.admission_year = each.clearance_id.application_id.admission_year
            each.admission_number = each.clearance_id.application_id.admission_number
            each.application_number = each.clearance_id.application_id.tc_application_no
            each.roll_no = student.roll_no

    def print_application(self):
        attendance_api_url = http.request.env['ir.config_parameter'].sudo().get_param('attendance_api_url')
        return {
            'type': 'ir.actions.act_url',
            'url': '%s/tc/tcapplicationpdf.php?ad=%s' % (attendance_api_url, self.admission_number),
            'target': 'new',
            # 'res_id': self.id,
        }

    def get_status(self):
        if self.env.user.name == 'A4':
            tc_form = self.env.ref('safi_students.tc_clearance_line_a4_form', False)
            user = self.env['res.users'].search([('name', '=', 'A3')])
            tc_clearance = self.env['tc.clearance.line'].search(
                [('section_id', '=', user.id), ('clearance_id', '=', self.clearance_id.id)])
            return {
                'name': _('TC Status'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'tc.clearance.line',
                'res_id': tc_clearance.id,
                'views': [(tc_form.id, 'form')],
                'view_id': tc_form.id,
                'target': 'new',
                # 'context': {'default_application_id': self.id},
            }


class TcApplicationFetch(models.TransientModel):
    _name = 'tc.application.wizard'

    def fetch_tc_applications(self):
        attendance_api_url = http.request.env['ir.config_parameter'].sudo().get_param('attendance_api_url')
        tc_application = self.env['tc.applications'].search([], order='tc_application_no DESC', limit=1)
        if tc_application:
            application_number = tc_application.tc_application_no
        else:
            application_number = 0
        url = '%s/tc/api/api.php?r=_tcappfrom&a=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09' % (
            attendance_api_url, application_number)
        val = urllib.request.urlopen(url).read(1000000).decode("utf-8")
        # raise UserError(str(val))
        val = json.loads(val)
        val = ast.literal_eval("%s" % (val))
        # raise UserError(str(val))
        for application in val:
            # raise UserError(type(application['approved']))
            programme = self.env['programme.programme'].sudo().search([('code', '=', application['programme'])])
            programme_admitted = self.env['programme.programme'].sudo().search([('code', '=', application['programmeadmitted'])])
            semester = self.env['semester.semester'].search([('name', '=', application['semester'])])
            exam_semester = self.env['semester.semester'].search([('name', '=', application['examsemester'])])
            values = {
                'tc_application_no': application['tcappno'],
                'admission_number': application['admissionno'],
                'student_name': application['name'],
                'dob': application['dob'],
                'admission_year': application['yearofadmission'],
                'admission_date': application['doa'],
                'date_of_leave': application['dol'],
                'programme_admitted_id': programme_admitted.id,
                'semester_admitted': application['semesteradmitted'],
                'programme_id': programme.id,
                'semester': application['semester'],
                'reason': application['reason'],
                'promotion': application['promotion'],
                'exam_semester': application['examsemester'],
                'exam_year': application['examyear'],
                'exam_register_number': application['exregno'],
                'exam_passed': application['expassed'],
                'date_of_application': application['dtapp'],
                'is_approved': int(application['approved']),
                'state': 'draft' if int(application['approved']) == 0 else 'approved'
            }
            # raise UserError(str(values))
            self.env['tc.applications'].sudo().create(values)
