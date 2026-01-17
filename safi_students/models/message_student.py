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


class StudentEmail(models.Model):
    _name = 'email.student'
    _description = 'Email Student'

    batch_year = fields.Selection(
        [(str(num), str(num)) for num in range(datetime.now().year - 4, datetime.now().year + 1)], string='Batch Year')
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG'), ('integrated', 'Integrated')])
    batch_ids = fields.Many2many('batch.batch')
    student_ids = fields.Many2many('student.student')
    message = fields.Html()
    subject = fields.Text()
    attachment = fields.Many2many('ir.attachment')
    date = fields.Date(default=fields.Date.today())
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], default='draft')

    def send_email(self):
        password = "erp@sias"
        sender_email = "erp@siasindia.org"
        if self.student_ids:
            students = self.env['student.student'].browse(self.student_ids.ids)
        else:
            students = self.env['student.student'].search([('batch_id', 'in', self.batch_ids.ids)])
        attachments = [(a['store_fname'], base64.b64decode(a['datas']), a['mimetype'])
                       for a in self.attachment.sudo().read(['store_fname', 'datas', 'mimetype']) if
                       a['datas'] is not False]
        for student in students:
            receiver_email = student.email
            message = MIMEMultipart("alternative")
            message["Subject"] = self.subject
            message["From"] = '%s <%s>' % (self.env.company.name, sender_email)
            message["To"] = student.email
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
            self.env['email.student.line'].create({'student_id': student.id, 'log_id': self.id})
            self.state = 'sent'

    def student_view(self):
        self.ensure_one()
        domain = [('log_id', '=', self.id)]
        # raise UserError(str(domain))
        return {
            'name': _('Send Email'),
            'domain': domain,
            'res_model': 'email.student.line',
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


class EmailStudentLine(models.Model):
    _name = 'email.student.line'
    _description = 'Email Student Line'

    student_id = fields.Many2one('student.student')
    log_id = fields.Many2one('email.student')


# class StudentMessage(models.TransientModel):
#     _name = 'message.student'
#     _description = 'Message Student'
#
#     batch_year = fields.Selection(
#         [(num, str(num)) for num in range(datetime.now().year - 4, datetime.now().year + 1)], string='Batch Year')
#     level = fields.Selection([('ug', 'UG'), ('pg', 'PG')])
#     batch_ids = fields.Many2many('batch.batch')
#     student_ids = fields.Many2many('student.student')
#     message = fields.Text()
#     subject = fields.Text()
#     attachment = fields.Many2many('ir.attachment')
#     date = fields.Datetime(default=datetime.now())
#
#     # def send_sms_message(self):
#     #     if self.student_ids:
#     #         students = self.env['student.student'].browse(self.student_ids.ids)
#     #     else:
#     #         students = self.env['student.student'].search([('batch_id', 'in', self.batch_ids.ids)])
#     #     username = 'farookcollege'
#     #     password = '42c23cng91gx62bjp'
#     #     sender = 'FCADMN'
#     #     message = self.message
#     #     for student in students:
#     #         mobile = student.mobile if student.mobile else student.phone
#     #         url = "http://sms.coolwrks.com/pushsms.php?username=%s&api_password=%s&sender=%s&to=%s&message=%s&priority=11" % (
#     #             username, password, sender, mobile, urllib.parse.quote(message))
#     #         # raise UserError(str(url))
#     #         urllib.request.urlopen(url)
#     #         # values = {
#     #         #     'student_id': student.id,
#     #         #     'message': message,
#     #         #     'date': datetime.now(),
#     #         #     'mobile': mobile,
#     #         # }
#     #         # self.env['student.message.log'].create(values)
#
#     def send_email(self):
#         if self.student_ids:
#             students = self.env['student.student'].browse(self.student_ids.ids)
#         else:
#             students = self.env['student.student'].search([('batch_id', 'in', self.batch_ids.ids)])
#         subject = self.subject
#         message = self.message
#         cc_recipients = []
#         for student in students:
#             cc_recipients.append(student.email)
#         to_recipient = cc_recipients.pop()
#         mail_pool = self.env['mail.mail']
#         values = {}
#         values.update({'subject': subject})
#         values.update({'email_to': to_recipient})
#         values.update({'email_cc': ','.join(cc_recipients)})
#         values.update({'body_html': message})
#         values.update({'body': message})
#         values.update({'attachment_ids': [(6, 0, self.attachment.ids)]})
#         msg_id = mail_pool.create(values)
#         msg_id.send()
#         print(msg_id.state)
#         # for student in students:
#
#         # values = {
#         #     'student_id': student.id,
#         #     'message': message,
#         #     'date': datetime.now(),
#         #     'mobile': mobile
#         # }
#         # self.env['student.message.log'].create(values)
#
#     @api.onchange('batch_year', 'level')
#     def onchange_batch_domain(self):
#         batch_domain = []
#         if self.level:
#             batch_domain.append(('programme_id.level', '=', self.level))
#         if self.batch_year:
#             batch_domain.append(('start_year', '=', self.batch_year))
#         return {'domain': {'batch_ids': batch_domain}}
#
#     # @api.model
#     # def get_batch_domain(self):
#     #     batch_domain = []
#     #     if self.start_year:
#     #         batch_domain = [('start_year', '=', self.start_year)]
#     #     # if self.level:
#     #     #     batch_domain.append(('programme_id.level', '=', self.level))
#     #     return batch_domain
