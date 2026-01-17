from odoo import fields, models, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning, UserError
import urllib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib, ssl


class EmailEmployee(models.Model):
    _name = 'email.employee'
    _description = 'Email Employee'

    employee_type = fields.Selection([('teaching', 'Teaching'), ('non_teaching', 'Non teaching')])
    department_ids = fields.Many2many('hr.department')
    employee_ids = fields.Many2many('hr.employee')
    message = fields.Html()
    subject = fields.Text()
    attachment = fields.Many2many('ir.attachment')
    date = fields.Datetime(default=fields.Date.today())
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], default='draft')

    def send_email(self):
        password = "erp@sias"
        sender_email = "erp@siasindia.org"
        domain = []
        if self.employee_type:
            domain.append(('employee_type', '=', self.employee_type))
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        if self.employee_ids:
            employees = self.env['hr.employee'].browse(self.employee_ids.ids)
        else:
            employees = self.env['hr.employee'].search(domain)
        attachments = [(a['store_fname'], base64.b64decode(a['datas']), a['mimetype'])
                       for a in self.attachment.sudo().read(['store_fname', 'datas', 'mimetype']) if
                       a['datas'] is not False]
        for employee in employees:
            receiver_email = employee.work_email
            message = MIMEMultipart("alternative")
            message["Subject"] = self.subject
            message["From"] = '%s <%s>' % (self.env.company.name, sender_email)
            message["To"] = employee.work_email
            mail_content = self.message
            content = MIMEText(mail_content, "html")
            message.attach(content)
            for (fname, fcontent, mime) in attachments:
                filename_rfc2047 = (fname)
                if mime and '/' in mime:
                    maintype, subtype = mime.split('/', 1)
                    part = MIMEBase(maintype, subtype)
                else:
                    part = MIMEBase('application', "octet-stream")
                part.set_param('name', filename_rfc2047)
                part.add_header('Content-Disposition', 'attachment', filename=filename_rfc2047)

                part.set_payload(fcontent)
                encoders.encode_base64(part)
                message.attach(part)
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(
                    sender_email, receiver_email, message.as_string()
                )
            self.env['email.employee.line'].create({'employee_id': employee.id, 'log_id': self.id})
            self.state = 'sent'

    @api.onchange('employee_type', 'department_ids')
    def onchange_employee_type(self):
        employee_domain = []
        if self.employee_type:
            employee_domain.append(('employee_type', '=', self.employee_type))
        if self.department_ids:
            employee_domain.append(('department_id', 'in', self.department_ids.ids))
        return {'domain': {'employee_ids': employee_domain}}

    def staff_view(self):
        self.ensure_one()
        domain = [('log_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Send Email'),
            'domain': domain,
            'res_model': 'email.employee.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                           Click Create for Entering Presentation Details
                                        </p>'''),
            'limit': 80,
            'context': {'default_log_id': self.id}
        }


class EmailEmployeeLine(models.Model):
    _name = 'email.employee.line'
    _description = 'Email Employee Line'

    employee_id = fields.Many2one('hr.employee')
    log_id = fields.Many2one('email.employee')
