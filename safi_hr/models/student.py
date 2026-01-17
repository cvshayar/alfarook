from odoo import fields, models, api


class Programme(models.Model):
    _inherit = 'programme.programme'

    department_id = fields.Many2one('hr.department', domain=[('department_type', '=', 'Academic')])


class Batch(models.Model):
    _inherit = 'batch.batch'

    adviser_ids = fields.One2many('employee.advisership', 'batch_id')
