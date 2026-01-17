import urllib
from datetime import datetime, date, timedelta

import pytz
import requests
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
import ast, json
from PIL import Image
from io import BytesIO
from odoo import http
from odoo.osv import expression
import base64
from odoo import modules


class Programme(models.Model):
    _name = 'programme.programme'
    _order = 'sort_order'
    _rec_name = 'pgm_display_name'

    name = fields.Char('Title')
    pgm_display_name = fields.Char('Display Name')
    code = fields.Integer()
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG'), ('integrated', 'Integrated'), ('PDC', 'PDC')])
    duration = fields.Selection([(str(num), str(num)) for num in range(1, 11)], 'Duration')
    # department_id = fields.Many2one('department.department')
    reg_no_code = fields.Char()
    reg_no_sl_no_max = fields.Char()
    is_self_finance = fields.Boolean(default=True)
    sort_order = fields.Integer()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        programme = self.search(['|', ('name', operator, name),
                                 ('code', operator, name)])  # here you need to pass the args as per your requirement.
        return programme.name_get()

    def unlink(self):
        for each in self:
            student = self.env['student.student'].search([('programme_id', '=', each.id), ('admission_number', '>', 0)])
            if len(student) > 0:
                raise UserError(str('You are not allowed to delete programme'))
            return super(Programme, self).unlink()


class Batch(models.Model):
    _name = 'batch.batch'
    _rec_name = 'complete_name'
    _order = 'start_year DESC, sort_order'

    name = fields.Char('Code')
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    # curriculum_id = fields.Many2one('curriculum.curriculum')
    start_year = fields.Integer('Start Year', default=datetime.now().year)
    current_semester_id = fields.Many2one('semester.semester', string="Current Semester")
    active = fields.Boolean(default=True)
    programme_id = fields.Many2one('programme.programme')
    sort_order = fields.Integer(related='programme_id.sort_order', store=True)
    strength = fields.Integer()
    division = fields.Char()

    @api.onchange('current_semester_id')
    def current_sem_onchange_(self):
        for student in self.env['student.student'].search(
                [('batch_id', '=', self._origin.id), ('tc_issued', '=', False)]):
            student.write({'semester_id': self.current_semester_id.id})

    @api.depends('start_year', 'programme_id', 'division')
    def _compute_complete_name(self):
        for batch in self:
            batch.complete_name = str(batch.programme_id.pgm_display_name if batch.programme_id else '') + ' ' + str(
                batch.start_year if batch.start_year else '') + str(batch.division if batch.division else '')

    def unlink(self):
        for each in self:
            student = self.env['student.student'].search([('batch_id', '=', each.id), ('admission_number', '>', 0)])
            if len(student) > 0:
                raise UserError(str('You are not allowed to delete batch'))
            return super(Batch, self).unlink()


class AdmissionCategory(models.Model):
    _name = 'admission.category'
    _rec_name = 'complete_name'

    name = fields.Char()
    group = fields.Selection([('Merit', 'Merit'), ('Management', 'Management')])
    complete_name = fields.Char(compute='compute_complete_name')

    @api.depends('group', 'name')
    def compute_complete_name(self):
        for each in self:
            if each.name and each.group:
                each.complete_name = each.name + '(' + each.group + ')'

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('admission_category_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(AdmissionCategory, self).unlink()


class SecondLanguage(models.Model):
    _name = 'second.language'
    _order = 'name'

    name = fields.Char()

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('second_language_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(SecondLanguage, self).unlink()


class FeeCategory(models.Model):
    _name = 'fee.category'

    name = fields.Char()

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('fee_category_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(FeeCategory, self).unlink()


class Religion(models.Model):
    _name = 'religion.religion'

    name = fields.Char()

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('religion_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(Religion, self).unlink()


class CasteCategory(models.Model):
    _name = 'caste.category'

    name = fields.Char('Category')
    sort_order = fields.Integer('Sort order')

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('caste_category_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(CasteCategory, self).unlink()


class Caste(models.Model):
    _name = 'caste.caste'

    name = fields.Char()
    category = fields.Many2one('caste.category')

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('caste_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(Caste, self).unlink()


class Hostel(models.Model):
    _name = 'hostel.hostel'

    name = fields.Char('Hostel')


class StateDistrict(models.Model):
    _name = 'state.district'

    @api.model
    def get_state(self):
        return self.env['res.country.state'].search([('name', '=', 'Kerala')])

    name = fields.Char()
    state_id = fields.Many2one('res.country.state', default=get_state)

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('district_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(StateDistrict, self).unlink()


class Taluk(models.Model):
    _name = 'taluk.taluk'
    _description = 'Taluk'

    name = fields.Char()
    district_id = fields.Many2one('state.district')

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('taluk_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(Taluk, self).unlink()


class Panchayath(models.Model):
    _name = 'panchayath.panchayath'
    _description = 'Panchayath'

    name = fields.Char()
    taluk_id = fields.Many2one('taluk.taluk')

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('panchayath_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(Panchayath, self).unlink()


class LocalSelfGovernment(models.Model):
    _name = 'local.self.government'
    _description = 'Local Self Government'

    name = fields.Char()
    lsg_type = fields.Selection(
        [('Panchayath', 'Panchayath'), ('Municipality', 'Municipality'), ('Corporation', 'Corporation')])

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('lsg_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(Panchayath, self).unlink()


class Semester(models.Model):
    _name = 'semester.semester'
    _description = 'Semester'

    name = fields.Char()

    def unlink(self):
        for each in self:
            if self.env['student.student'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('semester_id', '=', each.id)]):
                raise UserError(str('You are not allowed to delete'))
            return super(Semester, self).unlink()


class StudentStudent(models.Model):
    _name = 'student.student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def get_state(self):
        return self.env['res.country.state'].search([('name', '=', 'Kerala')])

    def get_nationality(self):
        return self.env['res.country'].search([('name', '=', 'India')])

    @api.model
    def get_fee_category(self):
        return self.env['fee.category'].search([('name', '=', 'General(Fee)')])

    image = fields.Binary('image', track_visibility='onchange', attachment=False)
    reg_no = fields.Char(string="Register Number", track_visibility='onchange')
    name = fields.Char(required=True, track_visibility='onchange')
    batch_id = fields.Many2one('batch.batch', track_visibility='onchange')
    nationality = fields.Many2one('res.country', default=get_nationality)
    disability_id = fields.Many2one('disabled.category')
    address = fields.Text()
    post = fields.Char()
    city = fields.Char()
    pin = fields.Integer()
    app_no = fields.Char('Application Number', track_visibility='onchange')
    programme_id = fields.Many2one('programme.programme', track_visibility='onchange', related='batch_id.programme_id',
                                   store=True)
    year_of_admission = fields.Integer(string='Year of Admission', track_visibility='onchange')
    date_of_admission = fields.Date('Date of Admission', track_visibility='onchange', default=fields.Date.today)
    tc_issued = fields.Boolean('TC Issued')
    index = fields.Float()
    roll_no = fields.Char('Roll Number', track_visibility='onchange')
    dob = fields.Date(track_visibility='onchange')
    email = fields.Char(track_visibility='onchange')
    mobile = fields.Char(track_visibility='onchange')
    phone = fields.Char(track_visibility='onchange')
    parent_relation = fields.Selection([('Father', 'Father'), ('Mother', 'Mother'), ('Other', 'Other')])
    admission_category_id = fields.Many2one('admission.category')
    is_hostel = fields.Boolean(string='Hostel')
    hostel_id = fields.Many2one('hostel.hostel')
    annual_income = fields.Float()
    caste_category_id = fields.Many2one('caste.category', related='caste_id.category', store=True,
                                        track_visibility='onchange')
    fee_category_id = fields.Many2one('fee.category', default=get_fee_category, track_visibility='onchange')
    second_language_id = fields.Many2one('second.language', track_visibility='onchange')
    semester_id = fields.Many2one('semester.semester', 'Semester', track_visibility='onchange')
    blood_group = fields.Selection(
        [('A+', 'A+'), ('B+', 'B+'), ('AB+', 'AB+'), ('O+', 'O+'), ('A-', 'A-'), ('B-', 'B-'), ('AB-', 'AB-'),
         ('O-', 'O-')], track_visibility='onchange')
    sports = fields.Boolean()
    gender = fields.Selection(string="Gender", selection=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                              track_visibility='onchange')
    parent_name = fields.Char()
    parent_email = fields.Char()
    parent_mobile = fields.Char()
    parent_job = fields.Char()
    parent_address = fields.Text()
    admission_number = fields.Integer(track_visibility='onchange', group_operator=False)
    roll_order = fields.Integer(track_visibility='onchange')
    religion_id = fields.Many2one('religion.religion', track_visibility='onchange')
    caste_id = fields.Many2one('caste.caste', track_visibility='onchange')
    ph = fields.Boolean('PH', track_visibility='onchange')
    self_finance = fields.Boolean('Self Finance', related='programme_id.is_self_finance', store=True)
    active = fields.Boolean('Active', default=True, track_visibility='onchange')
    tenth_board = fields.Char('10th Board')
    tenth_year = fields.Integer(string='10th Passed Year')
    tenth_month = fields.Selection(
        [('January', 'January'), ('February', 'February'), ('March', 'March'), ('April', 'April'), ('May', 'May'),
         ('June', 'June'), ('July', 'July'), ('August', 'August'), ('September', 'September'), ('October', 'October'),
         ('November', 'November'), ('December', 'December')],
        string='10th Passed Month')
    tenth_reg_no = fields.Char('10th Register Number')
    tenth_percentage = fields.Float('10th Percentage')
    tenth_school = fields.Char('10th Institution')
    plus2_stream = fields.Char('Plus2 Stream')
    plus2_board = fields.Char('Plus2 Board')
    plus2_year = fields.Integer(string='Plus2 Passed Year')
    plus2_month = fields.Selection(
        [('January', 'January'), ('February', 'February'), ('March', 'March'), ('April', 'April'), ('May', 'May'),
         ('June', 'June'), ('July', 'July'), ('August', 'August'), ('September', 'September'), ('October', 'October'),
         ('November', 'November'), ('December', 'December')],
        string='Plus2 Passed Month')
    place_of_birth = fields.Char(track_visibility='onchange')
    aadhar_number = fields.Char(track_visibility='onchange')
    plus2_reg_no = fields.Char('Plus2 Register Number')
    plus2_percentage = fields.Float('Plus2 Percentage')
    plus2_school = fields.Char('Plus2 Institution')
    university_stream = fields.Char('University Programme')
    university = fields.Char()
    university_year = fields.Integer(string='Passed Year')
    university_month = fields.Selection(
        [('January', 'January'), ('February', 'February'), ('March', 'March'), ('April', 'April'), ('May', 'May'),
         ('June', 'June'), ('July', 'July'), ('August', 'August'), ('September', 'September'), ('October', 'October'),
         ('November', 'November'), ('December', 'December')],
        string='University Passed Month')
    university_reg_no = fields.Char('University Register Number')
    university_percentage = fields.Float('University Percentage')
    pg_visible = fields.Boolean(default=False, compute='compute_pg_visibility')
    college = fields.Char('College')
    is_readmission = fields.Boolean()
    is_repeat_sem = fields.Boolean()
    repeat_batch_id = fields.Many2one('batch.batch', track_visibility='always')
    # repeat_sem_ids = fields.One2many('student.repeat.semester', 'student_id')
    is_senior_admission = fields.Boolean()
    state_id = fields.Many2one('res.country.state', default=get_state)
    district_id = fields.Many2one('state.district')
    tc_no = fields.Char('TC Number', track_visibility='onchange')
    tc_date = fields.Date('TC Date', track_visibility='onchange')
    tc_institution = fields.Char('TC Institution', track_visibility='onchange')
    tc_course = fields.Char('TC Course')
    state = fields.Selection([('draft', 'Draft'), ('admitted', 'Admitted')], default='draft')
    capid = fields.Char(track_visibility='onchange')
    tc_relation = fields.One2many('tc.issued.register', 'student_id')
    transfer_relation = fields.One2many('student.transfer', 'student_id')
    inter_transfer_relation = fields.One2many('student.transfer', 'new_student_id')
    disciplinary_relation = fields.One2many('disciplinary.actions.details', 'student_id')
    scholarship_relation = fields.One2many('scholarship.details', 'student_id')
    fee_relation = fields.One2many('fee.collection', 'student_id', domain=[('state', '=', 'paid')])
    taluk_id = fields.Many2one('taluk.taluk')
    panchayath_id = fields.Many2one('panchayath.panchayath')
    apl_bpl = fields.Selection([('APL', 'APL'), ('BPL', 'BPL')])
    lsg_type = fields.Selection(
        [('Panchayath', 'Panchayath'), ('Municipality', 'Municipality'), ('Corporation', 'Corporation')])
    nri = fields.Boolean()
    plus2_inst_country = fields.Many2one('res.country')
    plus2_inst_state = fields.Many2one('res.country.state')
    plus2_inst_district = fields.Many2one('state.district')
    spc = fields.Boolean()
    nss = fields.Boolean()
    scout = fields.Boolean()
    lakshadweep = fields.Boolean()
    whatsapp_no = fields.Char(track_visibility='onchange')
    lsg_id = fields.Many2one('local.self.government')
    remarks = fields.Text()
    semester_remark_ids = fields.One2many('student.semester.remarks', 'student_id')

    @api.model
    def create(self, vals):
        if vals['admission_number'] != 0:
            if self.env['student.student'].search(['|', ('active', '=', True), ('active', '=', False),
                                                   ('admission_number', '=', vals['admission_number'])]):
                raise UserError('Admission number must be unique')
        # if vals['reg_no']:
        #     if self.env['student.student'].search(
        #             ['|', ('active', '=', True), ('active', '=', False), ('reg_no', '=', vals['reg_no'])]):
        #         raise UserError('Register number must be unique')
        # if vals['is_senior_admission']:
        #     last_student = self.env['student.student'].search(
        #         ['|', ('active', '=', True), ('active', '=', False), ('selffinance', '=', vals['selffinance'])],
        #         order='admission_number DESC', limit=1)
        #     vals['admission_number'] = last_student.admission_number + 1
        vals['name'] = vals['name'].upper()
        vals['state'] = 'admitted'
        res = super(StudentStudent, self).create(vals)
        res.load_fee()
        return res

    @api.onchange('roll_no')
    def onchange_roll_number(self):
        if self.roll_no:
            self.roll_order = self.roll_no

    @api.onchange('date_of_admission')
    def onchange_date_of_admission(self):
        if self.date_of_admission.strftime('%B') in ['January', 'February', 'March', 'April', 'May']:
            self.year_of_admission = self.date_of_admission.year - 1
        else:
            self.year_of_admission = self.date_of_admission.year

    def unlink(self):
        for each in self:
            if each.tc_issued:
                raise UserError(str('You are not allowed to delete student'))
            if each.admission_number > 0:
                raise UserError(str('You are not allowed to delete student'))
            return super(StudentStudent, self).unlink()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        partners = self.search(
            ['|', '|', '|', ('name', operator, name), ('admission_number', operator, name), ('app_no', operator, name),
             ('email', operator, name)])  # here you need to pass the args as per your requirement.
        return partners.name_get()

    @api.onchange('batch_id')
    def onchange_batch_id(self):
        self.programme_id = self.batch_id.programme_id
        self.semester_id = self.batch_id.current_semester_id

    def toggle_active(self):
        self.write({'active': True, 'semester_id': self.batch_id.current_semester_id.id})

    def view_fee_status(self):
        self.ensure_one()
        domain = [('student_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Fee Dues'),
            'domain': domain,
            'res_model': 'student.fee.dues',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                               Click Create for Entering Student Fee Dues
                                            </p>'''),
            'limit': 80,
            'context': {'default_student_id': self.id}
        }

    @api.depends('programme_id')
    def compute_pg_visibility(self):
        for each in self:
            if each.programme_id.level == 'pg':
                each.pg_visible = True
            else:
                each.pg_visible = False

    @api.onchange('state_id')
    def fc_onchange_state_id(self):
        if self.state_id:
            domain = [('state_id', '=', self.state_id.id)]
            return {'domain': {'district_id': domain}}

    @api.onchange('app_no')
    def fetch_student_details(self):
        if self.state == 'draft' and self.app_no and self.programme_id:
            application_api_url = http.request.env['ir.config_parameter'].sudo().get_param('application_api_url')
            if self.programme_id.level == 'ug':
                url = '%s/api/api.php?r=_ugapplicant&a=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09' % (
                    application_api_url, self.app_no)
            else:
                url = '%s/api/api.php?r=_pgapplicant&a=%s&k=ckxVclF0SUxBUm9OemhpWVUrWTJyZz09' % (
                    application_api_url, self.app_no)
            val = urllib.request.urlopen(url).read(1000000).decode("utf-8")
            val = json.loads(val)
            val = ast.literal_eval("%s" % val)
            try:
                tc_date = datetime.datetime.strptime(val['applicantdetails']['tcdate'], '%Y-%m-%d')
            except:
                tc_date = ''
            try:
                if val['applicantdetails']['qemonth'] == 'JAN':
                    plus2_month = 'January'
                elif val['applicantdetails']['qemonth'] == 'FEB':
                    plus2_month = 'February'
                elif val['applicantdetails']['qemonth'] == 'FEB':
                    plus2_month = 'February'
                elif val['applicantdetails']['qemonth'] == 'MAR':
                    plus2_month = 'March'
                elif val['applicantdetails']['qemonth'] == 'APR':
                    plus2_month = 'April'
                elif val['applicantdetails']['qemonth'] == 'MAY':
                    plus2_month = 'May'
                elif val['applicantdetails']['qemonth'] == 'JUN':
                    plus2_month = 'June'
                elif val['applicantdetails']['qemonth'] == 'JUL':
                    plus2_month = 'July'
                elif val['applicantdetails']['qemonth'] == 'AUG':
                    plus2_month = 'August'
                elif val['applicantdetails']['qemonth'] == 'SEP':
                    plus2_month = 'September'
                elif val['applicantdetails']['qemonth'] == 'OCT':
                    plus2_month = 'October'
                elif val['applicantdetails']['qemonth'] == 'NOV':
                    plus2_month = 'November'
                else:
                    plus2_month = 'December'
                if val['applicantdetails']['tenthmonth'] == 'JAN':
                    tenth_month = 'January'
                elif val['applicantdetails']['tenthmonth'] == 'FEB':
                    tenth_month = 'February'
                elif val['applicantdetails']['tenthmonth'] == 'FEB':
                    tenth_month = 'February'
                elif val['applicantdetails']['tenthmonth'] == 'MAR':
                    tenth_month = 'March'
                elif val['applicantdetails']['tenthmonth'] == 'APR':
                    tenth_month = 'April'
                elif val['applicantdetails']['tenthmonth'] == 'MAY':
                    tenth_month = 'May'
                elif val['applicantdetails']['tenthmonth'] == 'JUN':
                    tenth_month = 'June'
                elif val['applicantdetails']['tenthmonth'] == 'JUL':
                    tenth_month = 'July'
                elif val['applicantdetails']['tenthmonth'] == 'AUG':
                    tenth_month = 'August'
                elif val['applicantdetails']['tenthmonth'] == 'SEP':
                    tenth_month = 'September'
                elif val['applicantdetails']['tenthmonth'] == 'OCT':
                    tenth_month = 'October'
                elif val['applicantdetails']['tenthmonth'] == 'NOV':
                    tenth_month = 'November'
                else:
                    tenth_month = 'December'
                if val['applicantdetails']['nationality']:
                    nationality = self.env['res.country'].search(
                        [('code', '=', val['applicantdetails']['nationality'])])
                if val['applicantdetails']['district']:
                    district = self.env['state.district'].search(
                        [('name', '=', val['applicantdetails']['district'].upper())])
                caste = ''
                if val['applicantdetails']['caste']:
                    caste = self.env['caste.caste'].search([('name', '=', val['applicantdetails']['caste']['caste'])])
                    if not caste:
                        caste = self.env['caste.caste'].sudo().create(
                            {'name': val['applicantdetails']['caste']['caste']})
                    if len(caste) > 1:
                        caste = ''
                if val['applicantdetails']['religion']:
                    religion = self.env['religion.religion'].search(
                        [('name', '=', val['applicantdetails']['religion'])])
                    if val['applicantdetails']['religion'] == 'Muslim':
                        religion = self.env['religion.religion'].search([('name', '=', 'Islam')])
                    if not religion:
                        religion = self.env['religion.religion'].create({'name': val['applicantdetails']['religion']})
                    if len(religion) > 1:
                        religion = ''
                        # raise UserError(str(val['pin']))
                image_string = ''
                response = requests.get(val['photourl'])
                if response:
                    Image.open(BytesIO(response.content))
                    image_string = base64.encodebytes(urllib.request.urlopen(val['photourl']).read())
                if self.programme_id.level in ['ug', 'integrated']:
                    index_list = list(
                        filter(lambda person: person['ccode'] == self.programme_id.code, val['ranklists']))
                else:
                    index_list = [{'index': val['fis']}]
                self.name = val['applname'].upper() if val['applname'] else ''
                self.address = '\n'.join(val['address'].split(',')) if val['address'] else ''
                self.pin = int(val['pin'].replace(' ', '')) if val['pin'] else 0
                self.dob = val['dob'] if val['dob'] else ''
                self.ph = int(val['ph']) if val['ph'] else ''
                self.aadhar_number = val['aadhaar'] if val['aadhaar'] else ''
                self.email = val['email'] if val['email'] else ''
                self.mobile = val['mobile'] if val['mobile'] else ''
                self.phone = val['phone'] if val['phone'] else ''
                self.nationality = nationality.id if nationality else ''
                self.place_of_birth = val['applicantdetails']['placebirth'].upper() if val['applicantdetails'][
                    'placebirth'] else ''
                self.district_id = district.id if district else ''
                self.caste_id = caste.id if caste else ''
                self.parent_name = val['applicantdetails']['guardian'].upper() if val['applicantdetails'][
                    'guardian'] else ''
                self.parent_relation = val['applicantdetails']['grelation'] if val['applicantdetails'][
                    'grelation'] else ''
                self.parent_job = val['applicantdetails']['goccupation'] if val['applicantdetails'][
                    'goccupation'] else ''
                self.parent_mobile = val['applicantdetails']['gphone'] if val['applicantdetails']['gphone'] else ''
                self.annual_income = val['applicantdetails']['gincome'] if val['applicantdetails']['gincome'] else ''
                self.gender = val['applicantdetails']['gender'].lower() if val['applicantdetails']['gender'] else ''
                self.blood_group = val['applicantdetails']['bloodgroup'] if val['applicantdetails'][
                    'bloodgroup'] else ''
                self.image = image_string if image_string else ''
                self.tenth_reg_no = val['applicantdetails']['tenthregno'] if val['applicantdetails'][
                    'tenthregno'] else ''
                self.tenth_board = val['applicantdetails']['tenthboard'].upper() if val['applicantdetails'][
                    'tenthboard'] else ''
                self.tenth_year = val['applicantdetails']['tenthyear'] if val['applicantdetails']['tenthyear'] else ''
                self.tenth_month = tenth_month
                # 'tenth_month': val['applicantdetails']['tenthmonth'],
                self.tenth_school = val['applicantdetails']['tenthinst'].upper() if val['applicantdetails'][
                    'tenthinst'] else ''
                # raise UserError(type(val['applicantdetails']['tenthper']))
                tenth_percentage_str = str(val['applicantdetails']['tenthper']) if val['applicantdetails'][
                    'tenthper'] else '0.0'
                tenth_percentage = ''
                if val['applicantdetails']['tenthper']:
                    for percentage in tuple(val['applicantdetails']['tenthper']):
                        tenth_percentage = str(tenth_percentage) + str(percentage)
                    tenth_percentage = tenth_percentage.replace('(', '')
                    tenth_percentage = tenth_percentage.replace(')', '')
                    tenth_percentage = tenth_percentage.replace(',', '')
                    tenth_percentage = tenth_percentage.lstrip('0')
                    self.tenth_percentage = float(tenth_percentage)
                if self.programme_id.level in ['ug', 'integrated']:
                    self.plus2_reg_no = val['applicantdetails']['qeregno'] if val['applicantdetails']['qeregno'] else ''
                    self.plus2_board = val['qexam'] if val['qexam'] else ''
                    self.plus2_stream = val['stream'].upper() if val['stream'] else ''
                    self.plus2_year = val['applicantdetails']['qeyearpass'] if val['applicantdetails'][
                        'qeyearpass'] else ''
                    self.plus2_school = val['applicantdetails']['qelastinst'].upper() if val['applicantdetails'][
                        'qelastinst'] else ''
                    self.plus2_percentage = val['plus2percentage'] if val['plus2percentage'] else ''
                else:
                    self.plus2_reg_no = val['applicantdetails']['plus2regno'] if val['applicantdetails'][
                        'plus2regno'] else ''
                    self.plus2_board = val['applicantdetails']['plus2board'] if val['applicantdetails'][
                        'plus2board'] else ''
                    self.plus2_stream = val['applicantdetails']['plus2stream'] if val['applicantdetails'][
                        'plus2stream'] else ''
                    self.plus2_year = val['applicantdetails']['plus2year'] if val['applicantdetails'][
                        'plus2year'] else ''
                    self.plus2_school = val['applicantdetails']['plus2inst'].upper() if val['applicantdetails'][
                        'plus2inst'] else ''
                    self.plus2_percentage = val['applicantdetails']['plus2per'] if val['applicantdetails'][
                        'plus2per'] else ''
                    self.university_reg_no = val['applicantdetails']['qeregno'] if val['applicantdetails'][
                        'qeregno'] else ''
                    self.university = val['uguniversity']['university'] if val['uguniversity']['university'] else ''
                    self.university_year = val['applicantdetails']['qeyearpass'] if val['applicantdetails'][
                        'qeyearpass'] else ''
                    self.university_month = plus2_month
                    self.university_stream = val['ugstudied'] if val['ugstudied'] else ''
                    self.college = val['applicantdetails']['qelastinst'] if val['applicantdetails'][
                        'qelastinst'] else ''
                    self.university_percentage = val['ugpercentage'] if val['ugpercentage'] else ''
                self.plus2_month = plus2_month
                # self.plus2_year = val['applicantdetails']['qeyearpass'] if val['applicantdetails']['qeyearpass'] else ''
                # self.plus2_school = val['applicantdetails']['qelastinst'].upper() if val['applicantdetails']['qelastinst'] else ''
                # self.plus2_percentage = val['plus2percentage'] if val['plus2percentage'] else ''
                self.index = index_list[0]['index'] if index_list else ''
                self.tc_no = val['applicantdetails']['tcno'] if val['applicantdetails']['tcno'] else ''
                self.tc_date = tc_date
                self.tc_institution = val['applicantdetails']['tcinst'].upper() if val['applicantdetails'][
                    'tcinst'] else ''
                self.tc_course = val['applicantdetails']['tccourse'] if val['applicantdetails']['tccourse'] else ''
                self.post = val['applicantdetails']['post'] if val['applicantdetails']['post'] else ''
                self.city = val['applicantdetails']['place'] if val['applicantdetails']['place'] else ''
                self.capid = val['applicantdetails']['capid'] if val['applicantdetails']['capid'] else ''
                self.religion_id = religion.id if religion else ''
                if val['applicantdetails']['instcountry']:
                    country = self.env['res.country'].search([('code', '=', val['applicantdetails']['instcountry'])]).id
                    self.plus2_inst_country = country
                if val['applicantdetails']['inststate']:
                    state = self.env['res.country.state'].search(
                        [('name', '=', val['applicantdetails']['inststate'].capitalize())]).id
                    self.plus2_inst_state = state
                if val['applicantdetails']['instdistrict']:
                    district = self.env['state.district'].search(
                        [('name', '=', val['applicantdetails']['instdistrict'].upper())]).id
                    self.plus2_inst_district = district
                self.spc = int(val['spc'])
                self.nss = int(val['nss'])
                self.scout = int(val['scout'])
                self.lakshadweep = int(val['ldweep'])
                self.nri = int(val['applicantdetails']['nri'])
                self.lsg_type = val['applicantdetails']['lsgtype']
                if val['applicantdetails']['lsg']:
                    lsg = self.env['local.self.government'].search(
                        [('name', '=', val['applicantdetails']['lsg'].capitalize())]).id
                    if not lsg:
                        lsg = self.env['local.self.government'].sudo().create(
                            {'name': val['applicantdetails']['lsg'].capitalize(),
                             'lsg_type': val['applicantdetails']['lsgtype']}).id
                    self.lsg_id = lsg
                self.apl_bpl = val['applicantdetails']['bpl']
                self.whatsapp_no = val['applicantdetails']['whatsapp']

            except UserError as e:
                # let UserErrors (messages) bubble up
                raise e
            except Exception as e:
                raise UserError(_('%s') % e)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default['admission_number'] = 0
        default['reg_no'] = ''
        default['roll_no'] = ''
        default['roll_order'] = 0
        default['tc_issued'] = False
        if not self.parent_relation:
            default['parent_relation'] = ''
        if not self.gender:
            default['gender'] = ''
        if not self.blood_group:
            default['blood_group'] = ''
        if self.programme_id.level == 'ug':
            default['university_month'] = ''
        else:
            default['tenth_month'] = ''
            default['plus2_month'] = ''
        return super(StudentStudent, self).copy(default=default)

    def load_fee_due(self):
        tc_form = self.env.ref('safi_students.batch_fee_load_form_view', False)
        semester = self.env['semester.semester'].search([('name', '=', str(int(self.semester_id.name) + 1))])
        if fields.Date.today().strftime('%B') in ['January', 'February', 'March', 'April', 'May']:
            academic_year = date.today().year - 1
        else:
            academic_year = date.today().year
        return {
            'name': _('Load Fee'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'batch.fee.load',
            'views': [(tc_form.id, 'form')],
            'view_id': tc_form.id,
            'target': 'new',
            'context': {'default_student_id': self.id, 'default_semester_id': semester.id, 'default_academic_year': academic_year, 'default_type': 'Student'},
        }

    def load_fee(self):
        if self.semester_id.name in ['1', '2']:
            academic_year = self.batch_id.start_year
        elif self.semester_id.name in ['3', '4']:
            academic_year = self.batch_id.start_year + 1
        else:
            academic_year = self.batch_id.start_year + 2
        programme_fee = self.env['programme.fee'].search(
            [('programme_ids', 'in', self.programme_id.ids), ('fee_category_ids', 'in', self.fee_category_id.ids),
             ('academic_year', '=', academic_year), ('semester_id', '=', self.semester_id.id),
             ('state', '=', 'confirmed')])
        for each in programme_fee.programme_line:
            values = {
                'student_id': self.id,
                'fee_id': each.fee_id.id,
                'gross_payable_amount': each.amount,
                'net_payable_amount': each.amount,
                'semester_id': self.semester_id.id,
                # 'installment_id': each.programme_fee_id.installment_id.id,
                'academic_year': academic_year
            }
            fee_dues = self.env['student.fee.dues'].create(values)
            fee_dues.calculate_net_payable_amount()

    @api.constrains('admission_number')
    def check_duplicate_admission_number(self):
        if self.admission_number > 0:
            student = self.env['student.student'].search([('admission_number', '=', self.admission_number), ('id', '!=', self.id)])
            if student:
                raise UserError('Admission number already exist')


# Roll Number Allotment
class StudentRollNumber(models.TransientModel):
    _name = 'student.roll.number'

    batch_id = fields.Many2one('batch.batch')
    start_roll_no = fields.Char('Starting Roll Number')
    line_ids = fields.One2many('student.roll.number.line', 'roll_id')

    @api.onchange('batch_id')
    def onchange_batch_id(self):
        self.line_ids = False
        new_lines = self.env['student.roll.number.line']
        roll_no = self.start_roll_no if self.start_roll_no else ''
        for line in self.env['student.student'].search(
                [('batch_id', '=', self.batch_id.id), ('admission_number', '>', 0), ('tc_issued', '=', False)],
                order='second_language_id, gender,name'):
            roll_no = int(roll_no) + 1 if roll_no else ''
            data = {'student_id': line.id, 'roll_no': roll_no if self.start_roll_no else line.roll_no,
                    'roll_order': roll_no if self.start_roll_no else line.roll_order,
                    'second_language': line.second_language_id}
            new_line = new_lines.new(data)
            new_lines += new_line
        self.line_ids += new_lines

    @api.onchange('start_roll_no')
    def onchange_roll_no(self):
        if self.start_roll_no:
            roll_no = int(self.start_roll_no) - 1
            for line in self.line_ids:
                roll_no = int(roll_no) + 1
                line.roll_no = roll_no
                line.roll_order = roll_no

    def generate_roll_no(self):
        for line in self.line_ids:
            line.student_id.write({'roll_no': line.roll_no, 'roll_order': line.roll_order})


class StudentRollNumberLine(models.TransientModel):
    _name = 'student.roll.number.line'

    roll_id = fields.Many2one('student.roll.number')
    student_id = fields.Many2one('student.student')
    roll_no = fields.Char()
    roll_order = fields.Integer()
    second_language = fields.Many2one('second.language')


# Batch Promotion
class BatchPromotion(models.TransientModel):
    _name = 'batch.promotion'
    _description = 'Batch Promotion'

    start_year = fields.Selection(
        [(str(num), str(num)) for num in range(fields.Date.today().year - 4, fields.Date.today().year + 1)],
        string='Start Year')
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG'), ('integrated', 'Integrated')])
    batch_ids = fields.Many2many('batch.batch')
    student_ids = fields.Many2many('student.student')

    def promote_batch(self):
        for student in self.student_ids:
            values = {
                'admission_number': student.admission_number,
                'student_id': student.id,
                'semester_id': student.batch_id.current_semester_id.id,
                'date': fields.Date.today()
            }
            self.env['student.non.promotion'].create(values)
            student.write({'active': False})
        for batch in self.batch_ids:
            sem = int(batch.current_semester_id.name) + 1
            if sem > int(batch.programme_id.duration):
                raise UserError(str('You cannot promote'))
            semester = self.env['semester.semester'].search([('name', '=', str(sem))])
            batch.update({'current_semester_id': semester.id})
            for student in self.env['student.student'].search(
                    [('batch_id', '=', batch.id), ('tc_issued', '=', False)]):
                student.write({'semester_id': semester.id})

    @api.onchange('start_year', 'level')
    def onchange_batch_domain(self):
        batch_domain = []
        if self.level:
            batch_domain.append(('programme_id.level', '=', self.level))
        if self.start_year:
            batch_domain.append(('start_year', '=', self.start_year))
        return {'domain': {'batch_ids': batch_domain}}


class StudentNonPromotion(models.Model):
    _name = 'student.non.promotion'
    _description = 'StudentNonPromotion'

    date = fields.Date()
    admission_number = fields.Integer()
    student_id = fields.Many2one('student.student')
    batch_id = fields.Many2one('batch.batch', related='student_id.batch_id', store=True)
    semester_id = fields.Many2one('semester.semester')

    @api.onchange('admission_number')
    def _onchange_admission_number(self):
        if self.admission_number:
            self.student_id = self.env['student.student'].search(['|', ('active', '=', True), ('active', '=', False),
                                                                  ('admission_number', '=', self.admission_number)]).id


class Scholarship(models.Model):
    _name = 'scholarship.scholarship'

    name = fields.Char()


class ScholarshipDetails(models.Model):
    _name = 'scholarship.details'
    _description = 'Scholarship details'

    student_id = fields.Many2one('student.student', required=True)
    amount = fields.Integer()
    scholarship_id = fields.Many2one('scholarship.scholarship', required=True)
    semester = fields.Many2one('semester.semester', 'Semester', required=True)
    batch_id = fields.Many2one('batch.batch', related='student_id.batch_id', store=True)
    admission_number = fields.Integer(related='student_id.admission_number', store=True)
    remarks = fields.Text()
    date = fields.Date()

    @api.model
    def create(self, values):
        res = super(ScholarshipDetails, self).create(values)
        res.update_student_dues()
        return res

    @api.onchange('student_id', 'scholarship_id', 'semester')
    def onchange_student(self):
        if self.student_id and self.scholarship_id and self.semester:
            scholarship = self.env['scholarship.details'].search(
                [('scholarship_id', '=', self.scholarship_id.id), ('student_id', '=', self.student_id.id),
                 ('semester', '=', self.semester.id)])
            if scholarship:
                raise UserError(_('Already entered'))

    def update_student_dues(self):
        tuition_fee = self.env['student.fee.dues'].search(
            [('student_id', '=', self.student_id.id), ('semester_id', '=', self.semester.id),
             ('fee_id.name', '=', 'Tuition Fee')])
        if tuition_fee:
            tuition_fee.update({'scholarship_amount': (tuition_fee.scholarship_amount if tuition_fee.scholarship_amount > 0 else 0) +  self.amount})
            tuition_fee.calculate_net_payable_amount()


class DisciplinaryActions(models.Model):
    _name = 'disciplinary.actions'

    name = fields.Char()


class DisciplinaryDetails(models.Model):
    _name = 'disciplinary.actions.details'
    _description = 'Disciplinary action details'

    student_id = fields.Many2one('student.student', domain=[('tc_issued', '=', False)], required=True)
    disciplinary_id = fields.Many2one('disciplinary.actions', string='Action')
    from_date = fields.Date('Start date')
    to_date = fields.Date('End date')
    semester = fields.Many2one('semester.semester', 'Semester')
    remarks = fields.Text()


#     Student Repaeat Semester


class StudentRepeatSemester(models.Model):
    _name = 'student.repeat.semester'
    _description = 'Student Repeat Semester'

    student_id = fields.Many2one('student.student')
    admission_number = fields.Integer()
    batch_id = fields.Many2one('batch.batch')
    date = fields.Date(default=fields.Date.today())
    old_batch_id = fields.Many2one('batch.batch')
    old_roll_no = fields.Char()
    roll_no = fields.Char()
    semester_id = fields.Many2one('semester.semester', 'Semester')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed')], default='draft')

    @api.onchange('student_id')
    def get_batch(self):
        if self.student_id:
            self.old_batch_id = self.student_id.batch_id
            self.admission_number = self.student_id.admission_number
            self.old_roll_no = self.student_id.roll_no

    def confirm_repeat(self):
        if self.batch_id.programme_id != self.old_batch_id.programme_id:
            raise UserError(str('Programme should be same'))
        self.student_id.write(
            {'is_repeat_sem': True, 'repeat_batch_id': self.batch_id.id, 'semester_id': self.semester_id.id,
             'programme_id': self.batch_id.programme_id.id, 'roll_no': self.roll_no})
        self.state = 'confirm'


#         Student Readmission

class StudentReadmission(models.Model):
    _name = 'student.readmission'
    _description = 'Student Readmission'

    student_id = fields.Many2one('student.student', domain=[('active', '=', False)])
    admission_number = fields.Integer()
    batch_id = fields.Many2one('batch.batch')
    date = fields.Date(default=fields.Date.today())
    state = fields.Selection([('draft', 'Draft'), ('admit', 'Admitted')], default='draft')
    new_student_id = fields.Many2one('student.student')

    @api.onchange('admission_number')
    def get_batch(self):
        if self.admission_number:
            self.student_id = self.env['student.student'].search(
                ['|', ('active', '=', False), ('active', '=', True), ('admission_number', '=', self.admission_number)])

    def confirm_readmission(self):
        # last_student = self.env['student.student'].search(['|', ('active', '=', False), ('active', '=', True), (
        #     'self_finance', '=', self.batch_id.programme_id.is_self_finance)], order='admission_number DESC', limit=1)
        if not self.student_id:
            raise UserError(str('No such Student'))
        new_student = self.student_id.copy()
        new_student.write({'batch_id': self.batch_id.id, 'programme_id': self.batch_id.programme_id.id,
                           'active': True, 'self_finance': self.batch_id.programme_id.is_self_finance,
                           'date_of_admission': fields.Date.today(),
                           'is_readmission': True, 'semester_id': self.batch_id.current_semester_id})
        self.new_student_id = new_student.id
        self.state = 'admit'


# Student Semester Remarks

class StudentSemesterRemarks(models.Model):
    _name = 'student.semester.remarks'
    _description = 'StudentSemesterRemarks'

    def get_current_user(self):
        return self.env.user.id

    semester_id = fields.Many2one('semester.semester')
    admission_number = fields.Integer(related='student_id.admission_number')
    batch_id = fields.Many2one('batch.batch', related='student_id.batch_id')
    student_id = fields.Many2one('student.student')
    remarks = fields.Text()
    user_id = fields.Many2one('res.users', default=get_current_user)
    course_id = fields.Many2one('course.course')
    domain = fields.Binary(compute='compute_course_domain')
    
    @api.depends('semester_id', 'batch_id')
    def compute_course_domain(self):
        for each in self:
            curriculum_courses = self.env['curriculum.curriculum'].search([('programme_ids', 'in', each.batch_id.programme_id.ids),
                 ('semester_id', '=', each.semester_id.id)]).mapped('course_ids')
            each.domain = [('id', 'in', curriculum_courses.ids)]


class BatchGeneration(models.TransientModel):
    _name = 'batch.generation'
    _description = 'BatchGeneration'

    batch_year = fields.Integer(default=fields.Date.today().year)
    programme_ids = fields.Many2many('programme.programme')
    semester_id = fields.Many2one('semester.semester')

    def generate_batch(self):
        for programme in self.programme_ids:
            if self.env['batch.batch'].search(
                    [('programme_id', '=', programme.id), ('start_year', '=', self.batch_year)]):
                raise UserError(_('Already generated for %s' % programme.pgm_display_name))
            values = {
                'programme_id': programme.id,
                'start_year': self.batch_year,
                'current_semester_id': self.semester_id.id
            }
            self.env['batch.batch'].create(values)
