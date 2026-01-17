from odoo import fields, models, api, _
from datetime import datetime, date, timedelta, time
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from dateutil.relativedelta import relativedelta
import calendar


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.type'

    is_commuted = fields.Boolean()
    is_sandwitch = fields.Boolean(default=False)
    is_halfpay = fields.Boolean()
    is_casual = fields.Boolean(default=False)
    is_duty = fields.Boolean(default=False)
    prefix = fields.Boolean()
    suffix = fields.Boolean()
    include_prefix = fields.Boolean()
    include_suffix = fields.Boolean()
    is_other = fields.Boolean()
    is_compensation = fields.Boolean()

    @api.onchange('unpaid')
    def onchange_unpaid(self):
        if self.unpaid:
            self.is_halfpay = False

    @api.onchange('is_halfpay')
    def onchange_halfpay(self):
        if self.is_halfpay:
            self.unpaid = False


class LeaveReasons(models.Model):
    _name = 'leave.reasons'
    _order = 'name ASC'

    name = fields.Char()


class DutyType(models.Model):
    _name = 'duty.type'
    _order = 'name ASC'

    name = fields.Char()


class LeaveRole(models.Model):
    _name = 'leave.role'
    _order = 'name ASC'

    name = fields.Char()


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # is_sandwitch = fields.Boolean(related='holiday_status_id.is_sandwitch')
    leave_reasons_id = fields.Many2one('leave.reasons')
    approve_date = fields.Date()
    is_commuted = fields.Boolean(default=False)
    is_visible = fields.Boolean(default=False, store=True)
    is_field_visible = fields.Integer(default=0, store=True)
    is_halfday_visible = fields.Boolean(default=False, compute='compute_halfday_visible', store=True)
    # employee_adj_id = fields.Many2one('hr.employee', 'Employee Adjusted')
    # status = fields.Selection(
    #     [('to_be_adjusted', 'To be Adjusted'), ('adjusted', 'Adjusted'), ('cancelled', 'Cancelled')],
    #     default='to_be_adjusted', string='Hour Adjustment Status')
    duty_type_id = fields.Many2one('duty.type', 'Type of the duty')
    venue = fields.Char()
    address = fields.Text()
    designation_id = fields.Many2one('hr.job')
    leave_role_id = fields.Many2one('leave.role', 'Role of applicant')
    role = fields.Char('Specify Role')
    call_letter_ids = fields.Many2many('ir.attachment', string="Attachment",
                                       help='You can attach the copy of your document', copy=False)
    leave_line = fields.One2many('hr.leave.line', 'leave_id')
    prefix = fields.Date()
    suffix = fields.Date()
    leave_address = fields.Text()

    def name_get(self):
        res = []
        for leave in self:
            if self.env.context.get('short_name'):
                if leave.leave_type_request_unit == 'hour':
                    res.append((leave.id, _("%s : %.2f hour(s)") % (
                        leave.name or leave.holiday_status_id.name, leave.number_of_hours_display)))
                else:
                    res.append((leave.id, _("%s %s : %.2f day(s)") % (
                        leave.name or leave.holiday_status_id.name, leave.request_date_from.strftime('%d/%m/%Y'),
                        leave.number_of_days_display)))
            else:
                if leave.holiday_type == 'company':
                    target = leave.mode_company_id.name
                elif leave.holiday_type == 'department':
                    target = leave.department_id.name
                elif leave.holiday_type == 'category':
                    target = leave.category_id.name
                else:
                    target = leave.employee_id.name
                if leave.leave_type_request_unit == 'hour':
                    res.append(
                        (leave.id,
                         _("%s on %s : %.2f hour(s)") %
                         (target, leave.holiday_status_id.name, leave.number_of_hours_display))
                    )
                else:
                    res.append(
                        (leave.id,
                         _("%s on %s %s : %.2f day(s)") %
                         (target, leave.holiday_status_id.name, leave.request_date_from.strftime('%d/%m/%Y'),
                          leave.number_of_days_display))
                    )
        return res

    @api.depends('holiday_status_id')
    def compute_halfday_visible(self):
        for leave in self:
            if leave.holiday_status_id.is_casual:
                leave.is_halfday_visible = True

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.holiday_type == 'employee':
            self.department_id = self.employee_id.department_id
            self.designation_id = self.employee_id.job_id

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        self.request_unit_half = False
        self.request_unit_hours = False
        self.request_unit_custom = False
        if self.holiday_status_id:
            if self.holiday_status_id.is_halfpay:
                self.is_visible = True
            else:
                self.is_visible = False
            # if self.holiday_status_id.is_casual:
            #     self.is_halfday_visible = True
            if self.holiday_status_id.is_duty:
                self.is_field_visible = 1
            elif self.holiday_status_id.prefix and not self.holiday_status_id.suffix:
                self.is_field_visible = 3
            elif self.holiday_status_id.suffix and not self.holiday_status_id.prefix:
                self.is_field_visible = 4
            elif self.holiday_status_id.suffix and self.holiday_status_id.prefix:
                self.is_field_visible = 5
            else:
                self.is_field_visible = 0

    @api.onchange('leave_role_id')
    def onchange_leave_role(self):
        if self.leave_role_id:
            if self.leave_role_id.name == 'Other':
                self.is_field_visible = 2
            else:
                self.is_field_visible = 1

    def action_approve(self):
        # Add code here
        super(HrLeave, self).action_approve()
        self.approve_date = date.today()

    @api.onchange('prefix', 'suffix', 'date_from', 'date_to', 'employee_id', 'is_commuted', 'holiday_status_id')
    def _onchange_leave_dates(self):
        if self.date_from and self.date_to:
            if self.is_commuted:
                self.number_of_days = 2 * self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)[
                    'days']
            else:
                self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)[
                    'days']
        else:
            self.number_of_days = 0

    #
    @api.depends('number_of_days', 'is_commuted')
    def _compute_number_of_days_display(self):
        for holiday in self:
            if holiday.is_commuted:
                holiday.number_of_days_display = holiday.number_of_days / 2
            else:
                holiday.number_of_days_display = holiday.number_of_days

    # def _get_number_of_days(self, date_from, date_to, employee_id):
    #     """ Returns a float equals to the timedelta between two dates given as string."""
    #     if self.holiday_status_id.include_prefix and self.prefix:
    #         date_from = datetime.combine(self.prefix, datetime.min.time())
    #     if self.holiday_status_id.include_suffix and self.suffix:
    #         date_to = datetime.combine(self.suffix, datetime.max.time())
    #     if employee_id:
    #         employee = self.env['hr.employee'].browse(employee_id)
    #         if self.holiday_status_id.is_sandwitch is True:
    #             calendar = self.env['resource.calendar'].search([('is_sandwitch', '=', True)])
    #             return employee.get_work_days_data(date_from, date_to, calendar=calendar)[
    #                 'days']
    #         else:
    #             # resource = self.env['resource.resource'].search([('user_id', '=', employee.user_id.id)])
    #             return employee.get_work_days_data(date_from, date_to)['days']
    #
    #     today_hours = self.env.user.company_id.resource_calendar_id.get_work_hours_count(
    #         datetime.combine(date_from.date(), time.min),
    #         datetime.combine(date_from.date(), time.max),
    #         False)
    #
    #     return self.env.user.company_id.resource_calendar_id.get_work_hours_count(date_from, date_to) / (
    #             today_hours or HOURS_PER_DAY)

    @api.model
    def create(self, values):
        """ Override to avoid automatic logging of creation """
        employee_id = values.get('employee_id', False)
        if not values.get('department_id'):
            values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})
        if not values.get('designation_id'):
            values.update({'designation_id': self.env['hr.employee'].browse(employee_id).job_id.id})
        holiday = super(HrLeave,
                        self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)).create(values)
        if self._context.get('import_file'):
            holiday._onchange_leave_dates()
        if not self._context.get('leave_fast_create'):
            holiday.add_follower(employee_id)
            if 'employee_id' in values:
                holiday._sync_employee_details()
            if not self._context.get('import_file'):
                holiday.activity_update()
        return holiday

    # def name_get(self):
    #     res = []
    #     for leave in self:
    #         if self.env.context.get('short_name'):
    #             if leave.leave_type_request_unit == 'hour':
    #                 res.append((leave.id, _("%s : %.2f hour(s)") % (
    #                     leave.name or leave.holiday_status_id.name, leave.number_of_hours_display)))
    #             else:
    #                 res.append((leave.id, _("%s : %.2f day(s)") % (
    #                     leave.name or leave.holiday_status_id.name, leave.number_of_days_display)))
    #         else:
    #             if leave.holiday_type == 'company':
    #                 target = leave.mode_company_id.name
    #             elif leave.holiday_type == 'department':
    #                 target = leave.department_id.name
    #             elif leave.holiday_type == 'category':
    #                 target = leave.category_id.name
    #             else:
    #                 target = leave.employee_id.name
    #             if leave.leave_type_request_unit == 'hour':
    #                 res.append(
    #                     (leave.id,
    #                      _("%s on %s : %.2f hour(s)") %
    #                      (target, leave.holiday_status_id.name, leave.number_of_hours_display))
    #                 )
    #             else:
    #                 res.append(
    #                     (leave.id,
    #                      _("%s on %s : %.2f day(s)") %
    #                      (target, leave.holiday_status_id.name, leave.number_of_days_display))
    #                 )
    #     return res

    def view_department_leave(self):
        # employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        if self.env.user.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            leaves = self.env['hr.leave'].search([])
        else:
            leaves = self.env['hr.leave'].sudo().search([('employee_id.leave_manager_id', '=', self.env.uid)])
        return {
            'name': 'Leaves',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', leaves.ids)],
            'context': {'search_default_approve': 1},
            'res_model': 'hr.leave',
            'target': 'current'
        }


class HrLeaveLine(models.Model):
    _name = 'hr.leave.line'
    _description = 'Hr Leave Line'

    def _get_teachers(self):
        lst = []
        for teacher in self.env['hr.employee'].sudo().search([('employee_type', '=', 'teaching')],
                                                             order='department_id'):
            lst.append((teacher.name + ' [' + teacher.department_id.name + ']',
                        teacher.name + ' [' + teacher.department_id.name + ']'))
        return lst

    hour = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    # staff_id = fields.Many2one('hr.employee', 'Adjusted With')
    staff = fields.Selection(_get_teachers)
    leave_id = fields.Many2one('hr.leave')
    is_cancel = fields.Boolean('Cancelled')


class EmployeeTitle(models.Model):
    _name = 'employee.title'

    name = fields.Char()


class InserviceCourse(models.Model):
    _name = 'inservice.course'
    _description = 'Inservice Course'
    _order = 'name ASC'

    name = fields.Char()


class University(models.Model):
    _name = 'university.university'
    _description = 'University'
    _order = 'name ASC'

    name = fields.Char()


class EmployeeInserviceCourse(models.Model):
    _name = 'employee.inservice'
    _description = 'Employee In-service Course'

    @api.model
    def get_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id

    name = fields.Char()
    department_id = fields.Many2one('hr.department')
    designation_id = fields.Many2one('hr.job')
    inservice_course_id = fields.Many2one('inservice.course')
    date_from = fields.Date('From')
    date_to = fields.Date('To')
    center = fields.Char('HRDC/Center')
    university_id = fields.Many2one('university.university')
    attachment_ids = fields.Many2many('ir.attachment')
    employee_id = fields.Many2one('hr.employee')

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.designation_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id


class EmployeeProgramme(models.Model):
    _name = 'employee.programme'
    _order = 'name ASC'

    name = fields.Char()


class QualificationLevel(models.Model):
    _name = 'qualification.level'
    _order = 'name ASC'

    name = fields.Char()


class HrQualification(models.Model):
    _name = 'hr.qualification'

    level_id = fields.Many2one('qualification.level', 'Qualification')
    employee_id = fields.Many2one('hr.employee')
    university_id = fields.Many2one('university.university')
    date = fields.Date()
    is_visible = fields.Boolean()
    programme_id = fields.Many2one('employee.programme')
    certificate_no = fields.Char('Certificate Number')
    phd_ids = fields.One2many('hr.phd', 'qualification_id')
    grade = fields.Selection(
        [('Rank Holder', 'Rank Holder'), ('Distinction', 'Distinction'), ('First Class', 'First Class'),
         ('Second Class', 'Second Class'), ('Third Class', 'Third Class')])

    @api.onchange('level_id')
    def onchange_level_id(self):
        if self.level_id.name == 'PhD' or self.level_id.name == 'MPhil':
            self.is_visible = True

    def phd_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('PhD'),
            'domain': domain,
            'res_model': 'hr.phd',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                       Click Create for Entering Presentation Details
                                    </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.employee_id.id, 'default_qualification_id': self.id}
        }


class HrPhD(models.Model):
    _name = 'hr.phd'
    _description = 'PhD'

    name = fields.Text('Topic')
    guide = fields.Char()
    employee_id = fields.Many2one('hr.employee', related='qualification_id.employee_id')
    qualification_id = fields.Many2one('hr.qualification', ondelete='cascade')

    # @api.model
    # def create(self, values):
    #     qualification = self.env['hr.qualification'].browse([values['qualification_id']])
    #     qualification.write({'is_visible': False})
    #     # Add code here
    #     return super(HrPhD, self).create(values)


class Department(models.Model):
    _inherit = "hr.department"
    _order = "sort_order"

    sort_order = fields.Integer()
    department_type = fields.Selection([('Administrative', 'Administrative'), ('Academic', 'Academic')])
    is_self_finance = fields.Boolean()
    stream = fields.Selection(
        [('Science', 'Science'), ('Arts', 'Arts'), ('Commerce', 'Commerce'), ('Management', 'Management'),
         ('Journalism', 'Journalism')])


class EmployeeDistrict(models.Model):
    _name = "res.state.district"

    name = fields.Char()
    state_id = fields.Many2one('res.country.state')


class HrReligion(models.Model):
    _name = 'hr.religion'
    _order = 'name ASC'

    name = fields.Char()


class VotingConstituency(models.Model):
    _name = 'voting.constituency'
    _order = 'name ASC'

    name = fields.Char()


class TeachingFund(models.Model):
    _name = 'teaching.fund'
    _order = 'name ASC'

    name = fields.Char()


class HrCaste(models.Model):
    _name = 'hr.caste'
    _description = 'HrCaste'
    _order = 'name ASC'

    name = fields.Char()


class Committee(models.Model):
    _name = 'committee.committee'
    _description = 'Committee'
    _order = 'name ASC'

    name = fields.Char()


class CommitteePosition(models.Model):
    _name = 'committee.position'
    _description = 'Committee Position'
    _order = 'name ASC'

    name = fields.Char()


class PresentationType(models.Model):
    _name = 'presentation.type'
    _description = 'Presentation Type'
    _order = 'name ASC'

    name = fields.Char()


class EmployeePublications(models.Model):
    _name = 'employee.publications'
    _description = 'Employee Publications'
    _rec_name = 'presentation_name'

    presentation_name = fields.Text('Title of Presentation/Publication')
    journal_name = fields.Text('Title of Journal/Conferences')
    # presentation_type = fields.Selection(
    #     [('invited_talk', 'Invited Talk'), ('seminar', 'Seminar'), ('journal', 'Journal'),
    #      ('presentation', 'Presentation'), ('publication', 'Publication')])
    presentation_type_id = fields.Many2one('presentation.type')
    date = fields.Date('Date of Presentation/ Publication')
    authorship = fields.Selection(
        [('First Author', 'First Author'), ('Second Author', 'Second Author'), ('Other', 'Other')])
    employee_id = fields.Many2one('hr.employee')
    year = fields.Integer(default=fields.Datetime.now().year)
    month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'), ('06', 'June'),
         ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'), ('11', 'November'),
         ('12', 'December')])
    place = fields.Char()
    publisher = fields.Char()
    volume = fields.Char(string='Volume No./ Pages')
    issn_no = fields.Char('ISSN No./ DOI')
    indexing_agency = fields.Char()


class EmployeeAdvisership(models.Model):
    _name = 'employee.advisership'
    _description = 'Employee Advisership'
    # _rec_name = 'presentation_name'

    batch_id = fields.Many2one('batch.batch')
    semester_id = fields.Many2one('semester.semester')
    employee_id = fields.Many2one('hr.employee')
    is_active = fields.Boolean(compute='get_active_status', store=True)

    @api.depends('batch_id', 'semester_id')
    def get_active_status(self):
        for each in self:
            if each.semester_id != each.batch_id.current_semester_id:
                each.is_active = False
            else:
                each.is_active = True

    @api.model
    def retire_employee(self):
        for each in self.env['employee.advisership'].search([]):
            if int(each.semester_id) != int(each.batch_id.current_semester_id):
                each.is_active = False
            else:
                each.is_active = True


class EmployeeCommittee(models.Model):
    _name = 'employee.committee'
    _description = 'Employee Committee'
    _rec_name = 'committee_id'

    position_id = fields.Many2one('committee.position')
    committee_id = fields.Many2one('committee.committee')
    employee_id = fields.Many2one('hr.employee')
    from_date = fields.Date()
    to_date = fields.Date()


class EmployeeResourcePerson(models.Model):
    _name = 'employee.resource.person'
    _description = 'Employee Resource Person'
    _rec_name = 'title'

    title = fields.Char()
    organiser = fields.Text('Organiser and Address')
    audience_type = fields.Selection([('Student', 'Student'), ('Faculty', 'Faculty'), ('NTS', 'NTS'), ('Public', 'Public'), ('Other', 'Other')])
    employee_id = fields.Many2one('hr.employee')
    date = fields.Date()


class ServiceStation(models.Model):
    _name = 'service.station'
    _description = 'Service Station'

    name = fields.Char()


class EmployeeServiceBookMovement(models.Model):
    _name = 'employee.service.book'
    _description = 'Employee Service Book'
    _rec_name = 'station_id'

    station_id = fields.Many2one('service.station')
    employee_id = fields.Many2one('hr.employee')
    date = fields.Date()
    remarks = fields.Text()


class BankBank(models.Model):
    _name = 'bank.bank'
    _description = 'BankBank'

    name = fields.Char()


class Department(models.Model):
    _inherit = "hr.department"
    _order = "sort_order"

    sort_order = fields.Integer()
    department_type = fields.Selection([('Administrative', 'Administrative'), ('Academic', 'Academic')])
    # is_self_finance = fields.Boolean()
    # stream = fields.Selection([('Science', 'Science'), ('Arts', 'Arts'), ('Commerce', 'Commerce'), ('Management', 'Management'), ('Journalism', 'Journalism')])


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    # _order = "sort_order"

    employee_type = fields.Selection(string="Employee Type",
                                     selection=[('teaching', 'Teaching'), ('non_teaching', 'Non Teaching')])
    employee_category = fields.Selection(string="Employee Category",
                                         selection=[('management', 'Management'), ('government', 'Government')])
    address = fields.Text()
    title = fields.Many2one('employee.title')
    pen_number = fields.Char()
    father_name = fields.Char('Name of Father')
    blood_group = fields.Selection(
        [('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'),
         ('O-', 'O-')])
    date_of_joining = fields.Date()
    aadhar_number = fields.Char()
    pan_number = fields.Char()
    voter_id = fields.Char('Voter ID')
    retirement_date = fields.Date()
    religion_id = fields.Many2one('hr.religion')
    caste_id = fields.Many2one('hr.caste')
    join_sequence = fields.Integer()
    approval_order = fields.Char('Approval Order No')
    approval_order_date = fields.Date('Approval Date')
    constituency_id = fields.Many2one('voting.constituency', 'Voting Constituency')
    # fund_id = fields.Many2one('teaching.fund')
    committee_ids = fields.Many2many('committee.committee')
    account_number = fields.Char('Bank Account Number')
    # deduction_ids = fields.One2many('employee.deduction', 'employee_id')
    ph = fields.Selection([('Yes', 'Yes'), ('No', 'No')])
    employee_title_id = fields.Many2one('employee.title')
    sort_order = fields.Integer()
    employee_inservice_ids = fields.One2many('employee.inservice', 'employee_id')
    employee_qualification_ids = fields.One2many('hr.qualification', 'employee_id')
    phd_ids = fields.One2many('hr.phd', 'employee_id')
    country_id = fields.Many2one('res.country')
    state_id = fields.Many2one('res.country.state')
    district_id = fields.Many2one('res.state.district')
    research_guide = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No')
    probation_date = fields.Date('Probation Period')
    superannuation_date = fields.Date()
    retirement_age = fields.Selection([('56', '56'), ('60', '60')], default='56')
    appointment_nature = fields.Selection(
        [('Permanent', 'Permanent'), ('Temporary', 'Temporary'), ('Contract', 'Contract'), ('Guest', 'Guest')],
        string='Nature of Appointment')
    place = fields.Char()
    post = fields.Char()
    pin = fields.Char()
    comm_address = fields.Text('Address')
    comm_place = fields.Char('Place')
    comm_post = fields.Char('Post')
    comm_pin = fields.Char('Pin')
    comm_country_id = fields.Many2one('res.country', 'Country')
    comm_state_id = fields.Many2one('res.country.state', 'State')
    comm_district_id = fields.Many2one('res.state.district', 'District')
    communication_bool = fields.Boolean(store=False)
    edit_access = fields.Boolean(compute='compute_edit_permission')
    # edit_access = fields.Boolean(default=True)
    branch = fields.Char()
    bank_id = fields.Many2one('bank.bank')
    ifsc_code = fields.Char()

    @api.depends('user_id')
    def compute_edit_permission(self):
        self.edit_access = True
        # else:
        #     self.edit_access = False

    @api.onchange('country_id')
    def fc_onchange_country_id(self):
        if self.country_id:
            domain = [('country_id', '=', self.country_id.id)]
            return {'domain': {'state_id': domain}}

    @api.onchange('communication_bool')
    def onchange_method(self):
        if self.communication_bool:
            self.comm_address = self.address
            self.comm_place = self.place
            self.comm_post = self.post
            self.comm_pin = self.pin
            self.comm_country_id = self.country_id
            self.comm_state_id = self.state_id
            self.comm_district_id = self.district_id

    @api.onchange('birthday')
    def onchange_join_date(self):
        if self.birthday:
            if self.retirement_age == '56':
                self.superannuation_date = self.birthday + relativedelta(years=56)
            else:
                self.superannuation_date = self.birthday + relativedelta(years=60)
            if self.birthday.strftime('%B') in ['March', 'April', 'May']:
                last_day = calendar.monthrange(self.birthday.year, self.birthday.month)[1]
                if self.retirement_age == '56':
                    self.retirement_date = '%s-%s-%s' % (self.birthday.year + 56, self.birthday.month, last_day)
                else:
                    self.retirement_date = '%s-%s-%s' % (self.birthday.year + 60, self.birthday.month, last_day)
            elif self.birthday.strftime('%B') in ['January', 'February']:
                if self.retirement_age == '56':
                    self.retirement_date = '%s-03-31' % (self.birthday.year + 56)
                else:
                    self.retirement_date = '%s-03-31' % (self.birthday.year + 60)
            else:
                if self.retirement_age == '56':
                    self.retirement_date = '%s-03-31' % (self.birthday.year + 57)
                else:
                    self.retirement_date = '%s-03-31' % (self.birthday.year + 61)

    @api.onchange('state_id')
    def fc_onchange_state_id(self):
        if self.state_id:
            domain = [('state_id', '=', self.state_id.id)]
            return {'domain': {'district_id': domain}}

    def inservice_course_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('In-service Course'),
            'domain': domain,
            'res_model': 'employee.inservice',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                       Click Create for Entering In-service Course Details
                                    </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }

    def qualification_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Qualifications'),
            'domain': domain,
            'res_model': 'hr.qualification',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                           Click Create for Entering Qualification Details
                                        </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }

    def publication_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Presentations'),
            'domain': domain,
            'res_model': 'employee.publications',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click Create for Entering Presentation Details
                                </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }

    def advisership_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Advisership'),
            'domain': domain,
            'res_model': 'employee.advisership',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                       Click Create for Entering Presentation Details
                                    </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }

    def committee_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Committee'),
            'domain': domain,
            'res_model': 'employee.committee',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                       Click Create for Entering Committee Details
                                    </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }

    def resource_person_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Invited Talks'),
            'domain': domain,
            'res_model': 'employee.resource.person',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                       Click Create for Entering Invited Talks Details
                                    </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }
