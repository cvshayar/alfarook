from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError


class ProgrammeFeeCollectionReportWizard(models.TransientModel):
    _name = 'programme.fee.collection.report'

    from_date = fields.Date()
    to_date = fields.Date()
    batch_ids = fields.Many2many('batch.batch')
    level = fields.Selection([('ug', 'UG'), ('pg', 'PG')])
    year = fields.Selection(
        [(str(num), str(num)) for num in range(datetime.now().year - 8, datetime.now().year + 1)],
        default=datetime.now().year, string='Year')
    fee_type = fields.Selection([('government', 'Government'), ('college', 'College')], default='government',
                                required=True)

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'programme.fee.collection.report', 'form': self.read()[0]}
        return self.env.ref('safi_students.programme_fee_collection_report_xlsx_id').report_action(self, data=datas, config=False)


class ProgrammeFeeCollectionReportXlsx(models.AbstractModel):
    _name = 'report.safi_students.programme_fee_collection_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Student Details")

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        vertcal_align = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        boldr = workbook.add_format({'bold': True, 'align': 'right', 'border': 1})
        boldl = workbook.add_format({'bold': True, 'align': 'left', 'border': 1})
        bold = workbook.add_format({'bold': True, 'border': 1})
        center = workbook.add_format({'align': 'center', 'border': 1})
        right = workbook.add_format({'align': 'right', 'border': 1})
        left = workbook.add_format({'align': 'left', 'border': 1})
        vertcal_align.set_rotation(90)
        vertcal_align.set_align('vcenter')
        boldc.set_align('vcenter')
        center.set_align('vcenter')
        right.set_align('vcenter')
        boldl.set_align('vcenter')
        left.set_align('vcenter')

        row = 4
        new_row = row + 1
        domain = [('state', '=', 'post')]
        if invoices.from_date:
            domain.append(('payment_date', '>=', invoices.from_date))
        if invoices.to_date:
            domain.append(('payment_date', '<=', invoices.to_date))
        col = 1
        query_list = []
        if invoices.batch_ids:
            batches = self.env['batch.batch'].browse(invoices.batch_ids.ids)
            domain.append(('batch_id', 'in', batches.ids))
        else:
            batches = self.env['batch.batch'].search(
                [('start_year', '=', invoices.year), ('programme_id.level', '=', invoices.level)])
            domain.append(('batch_id', 'in', batches.ids))
        fee_categories = self.env['fee.collection'].search(domain).mapped('fee_category_id')
        length = len(fee_categories)
        worksheet.merge_range(0, 0, 1, (length + 1), self.env.user.company_id.name, boldc)
        worksheet.merge_range(2, 0, 2, (length + 1), 'Fee Collections from %s to %s' % (
            invoices.from_date.strftime('%d/%m/%Y'), invoices.to_date.strftime('%d/%m/%Y')), boldc)
        for fee_category in fee_categories:
            worksheet.merge_range(3, col, row, col, fee_category.name, boldc)
            col += 1
            if invoices.fee_type == 'government':
                query_list.append(""" SUM(CASE WHEN fc.fee_category_id = """ + str(fee_category.id) + """ THEN gov.amount
                ELSE 0 END) AS gov_""" + str(fee_category.id) + """ """)
            else:
                query_list.append(""" SUM(CASE WHEN fc.fee_category_id = """ + str(fee_category.id) + """ THEN col.amount
                                ELSE 0 END) AS col_""" + str(fee_category.id) + """ """)
        first_query = """ SELECT pp.name, pp.id,  """
        if invoices.fee_type == 'government':
            last_query = """ SUM(gov.amount) AS total FROM fee_collection fc 
                         INNER JOIN fee_collection_line gov ON gov.fee_collection_id = fc.id
                         INNER JOIN batch_batch bb ON bb.id = fc.batch_id INNER JOIN 
                         programme_programme pp ON pp.id = bb.programme_id WHERE fc.payment_date BETWEEN %s AND %s
                         AND fc.state = 'post'
                         GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        else:
            last_query = """ SUM(col.amount) AS total FROM fee_collection fc 
                                     INNER JOIN fee_collection_line col ON col.fee_collection_id = fc.id
                                     INNER JOIN batch_batch bb ON bb.id = fc.batch_id INNER JOIN 
                                     programme_programme pp ON pp.id = bb.programme_id WHERE fc.payment_date BETWEEN %s AND %s
                                     AND fc.state = 'post'
                                     GROUP BY pp.name, pp.id, bb.id HAVING bb.id in %s ORDER BY pp.sort_order """
        if query_list:
            query = str(first_query) + str(','.join(query_list)) + ',' + str(last_query)
        else:
            query = str(first_query) + str(last_query)
        aided_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == False).ids
        self_batch = batches.filtered(lambda x: x.programme_id.is_self_finance == True).ids
        worksheet.merge_range(3, 0, row, 0, 'Programme', boldc)
        worksheet.merge_range(3, col, row, col, 'Total', boldc)
        if aided_batch:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(aided_batch)])
            aided_batch_count = self.env.cr.dictfetchall()
            for each in aided_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                batch_tot = {}
                for fee_category in fee_categories:
                    col += 1
                    if invoices.fee_type == 'government':
                        worksheet.write(row, col, each['gov_%d' % fee_category.id], right)
                    else:
                        worksheet.write(row, col, each['col_%d' % fee_category.id], right)
                col += 1
                worksheet.write(row, col, each['total'], right)
        if self_batch:
            if aided_batch:
                row += 2
                worksheet.merge_range(row, 0, row, (length + 1), 'Self Finance', boldc)
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, tuple(self_batch)])
            self_batch_count = self.env.cr.dictfetchall()
            for each in self_batch_count:
                row += 1
                col = 0
                worksheet.write(row, 0, each['name'], left)
                for fee_category in fee_categories:
                    col += 1
                    if invoices.fee_type == 'government':
                        worksheet.write(row, col, each['gov_%d' % fee_category.id], right)
                    else:
                        worksheet.write(row, col, each['col_%d' % fee_category.id], right)
                    # worksheet.write(row, col, each['gov_%d' % fee_category.id], right)
                col += 1
                worksheet.write(row, col, each['total'], right)

