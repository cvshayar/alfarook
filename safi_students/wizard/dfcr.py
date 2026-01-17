from odoo import api, fields, models
import datetime
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError


class DFCR(models.TransientModel):
    _name = 'dfcr.wizard'
    _description = 'DFCR Wizard'

    from_date = fields.Date(required=True, default=fields.Date.today())
    to_date = fields.Date(required=True, default=fields.Date.today())
    fee_type = fields.Selection([('government', 'Government'), ('college', 'College')], default='government',
                                required=True)

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'dfcr.wizard', 'form': self.read()[0]}
        return self.env.ref('safi_students.dfcr_xlsx_id').report_action(self, data=datas, config=False)


class DFCRSelfFinance(models.TransientModel):
    _name = 'dfcr.self_finance.wizard'
    _description = 'DFCR Self Finance Wizard'

    from_date = fields.Date(required=True, default=fields.Date.today())
    to_date = fields.Date(required=True, default=fields.Date.today())
    report_type = fields.Selection([('collection', 'Collection'), ('refund', 'Refund')], default='collection')
    receipt_mode = fields.Selection([('Cash', 'Cash'), ('Bank', 'Bank'), ('Card', 'Card'), ('Cheque', 'Cheque'), ('Online', 'Online')])

    # fee_type = fields.Selection([('government', 'Government'), ('college', 'College')], default='government',
    #                             required=True)

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'dfcr.self_finance.wizard', 'form': self.read()[0]}
        return self.env.ref('safi_students.dfcr_self_finance_xlsx_id').report_action(self, data=datas, config=False)


class DFCRXlsx(models.AbstractModel):
    _name = 'report.safi_students.dfcr_xlsx'
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

        row = 3
        new_row = row + 1
        length = len(self.env['fees.item'].search(
            [('payable', '=', 'Government'), ('is_other_fee', '!=', True),
             ('name', 'not in', ['Tuition Fee', 'Late Fee', 'Readmission Fee'])]))
        worksheet.merge_range(0, 0, 1, length + 14, self.env.user.company_id.name, boldc)
        worksheet.merge_range(2, 0, 2, length + 14, 'DAILY FEE COLLECTION REGISTER', boldc)

        worksheet.merge_range(row, 0, row + 7, 0, 'Date', boldc)
        worksheet.write(row + 8, 0, '1', boldc)
        worksheet.merge_range(row, 1, row + 7, 1, 'Name of the student', boldc)
        worksheet.write(row + 8, 1, '2', boldc)
        worksheet.merge_range(row, 2, row + 7, 2, 'Class', vertcal_align)
        worksheet.write(row + 8, 2, '3', boldc)
        worksheet.merge_range(row, 3, row + 7, 3, 'Roll No \nSubject', vertcal_align)
        worksheet.write(row + 8, 3, '4', boldc)
        worksheet.merge_range(row, 4, row + 7, 4, 'Receipt\nNo.', vertcal_align)
        worksheet.write(row + 8, 4, '5', boldc)
        worksheet.merge_range(row, 5, row + 7, 5, 'No. of terms\nof installments', vertcal_align)
        worksheet.write(row + 8, 5, '6', boldc)
        worksheet.merge_range(row, 6, row + 7, 6, 'Tuition Fees', boldc)
        worksheet.write(row + 8, 6, '7', boldc)
        worksheet.merge_range(row, 7, row + 7, 7, 'Fine', vertcal_align)
        worksheet.write(row + 8, 7, '8', boldc)
        worksheet.merge_range(row, 8, row + 7, 9, 'Late fee or\nRe. Ad. fee', vertcal_align)
        worksheet.merge_range(row + 8, 8, row + 8, 9, '9', boldc)
        col = 9
        val = {
            'tuition': 0,
            'late_fee': 0,
            'readmission': 0,
            'fine': 0,
            'total': 0,
            'other_col': 0,
            'other_lib': 0,
            'other_lab': 0,
            'other_phy': 0,
            'other_tot': 0,
            'gov_reg': 0,
            'spl_reg': 0,
            'registration_fee': 0,

        }
        i = 9
        for fee_item in self.env['fees.item'].search(
                [('payable', '=', 'Government'), ('is_other_fee', '=', False),
                 ('name', 'not in', ['Tuition Fee', 'Late Fee', 'Readmission Fee', 'Fine'])],
                order='sort_order ASC'):
            col += 1
            i += 1
            if fee_item.name == 'Registration Fee':
                worksheet.merge_range(row, col, row + 7, col + 1, '\n'.join(fee_item.name.split(' ')), vertcal_align)
                worksheet.merge_range(row + 8, col, row + 8, col + 1, i, boldc)
                col += 1
            val['fee_%d' % fee_item.id] = 0
            worksheet.merge_range(row, col, row + 7, col, '\n'.join(fee_item.name.split(' ')), vertcal_align)
            worksheet.write(row + 8, col, i, boldc)
        col += 1
        i += 1
        worksheet.merge_range(row, col, row + 7, col, 'Other Collection', vertcal_align)
        worksheet.write(row + 8, col, i, boldc)
        worksheet.merge_range(row, col + 1, row, col + 3, 'Miscellaneous', boldc)
        worksheet.merge_range(row + 1, col + 1, row + 7, col + 1, 'Library', vertcal_align)
        worksheet.write(row + 8, col + 1, i + 1, boldc)
        worksheet.merge_range(row + 1, col + 2, row + 7, col + 2, 'Laboratory', vertcal_align)
        worksheet.write(row + 8, col + 2, i + 2, boldc)
        worksheet.merge_range(row + 1, col + 3, row + 7, col + 3, 'Physical\nEducation', vertcal_align)
        worksheet.write(row + 8, col + 3, i + 3, boldc)
        worksheet.merge_range(row, col + 4, row + 7, col + 4, 'Total', boldc)
        worksheet.write(row + 8, col + 4, i + 4, boldc)
        row = 11
        i = 0
        student_fee_collections = self.env['fee.collection'].search(
            [('payment_date', '=', invoices.to_date), ('fee_type', '=', 'student'), ('state', '=', 'post'),
             ('batch_id.programme_id.is_self_finance', '=', False)], order='id ASC')
        header_list = []
        end = (len(student_fee_collections) // 30) + 1
        for j in range(1, end):
            header_list.append(j * 30)
        for each in student_fee_collections:
            i += 1
            row += 1
            worksheet.write(row, 0, str(each.payment_date.strftime('%d/%m/%Y')), center)
            worksheet.write(row, 1, each.student_id.name if each.student_id else each.paid_by, left)
            worksheet.write(row, 2, str(each.year) + ', ' + str(each.student_id.batch_id.complete_name), left)
            worksheet.write(row, 3, each.student_id.roll_no if each.student_id.roll_no else '', center)
            worksheet.write(row, 5, ','.join(each.installment_ids.mapped('name')) if each.installment_ids else '',
                            center)
            worksheet.write(row, 4, each.gov_fee_reference if each.gov_fee_reference else '', left)
            tuition_fee = each.fee_line.filtered(lambda x: x.fee_id.name == 'Tuition Fee').amount
            val['tuition'] += tuition_fee
            late_fee = each.fee_line.filtered(lambda x: x.fee_id.name == 'Late Fee').amount
            val['late_fee'] += late_fee
            readmission_fee = each.fee_line.filtered(lambda x: x.fee_id.name == 'Readmission Fee').amount
            val['readmission'] += readmission_fee
            fine = each.fee_line.filtered(lambda x: x.fee_id.name == 'Fine').amount
            val['fine'] += fine
            registration_fee = each.fee_line.filtered(lambda x: x.fee_id.name == 'Registration Fee').amount
            val['registration_fee'] += registration_fee
            if registration_fee > 0:
                val['gov_reg'] += 25
                val['spl_reg'] += 30
            # val['fine'] += each.government_fine
            worksheet.write(row, 6, tuition_fee if tuition_fee > 0 else '',
                            right)
            worksheet.write(row, 7, fine if fine > 0 else '', right)
            worksheet.write(row, 8, late_fee if late_fee > 0 else '', center)
            worksheet.write(row, 9, readmission_fee if readmission_fee > 0 else '', center)
            col = 9
            for fee_item in self.env['fees.item'].search(
                    [('payable', '=', 'Government'),
                     ('is_other_fee', '=', False),
                     ('name', 'not in', ['Tuition Fee', 'Late Fee', 'Readmission Fee', 'Fine'])],
                    order='sort_order ASC'):
                col += 1
                amount = each.fee_line.filtered(lambda x: x.fee_id.id == fee_item.id).amount
                val['fee_%d' % fee_item.id] += amount
                if fee_item.name == 'Registration Fee':
                    worksheet.merge_range(row, col, row, col + 1, amount if amount > 0 else '', right)
                    col += 1
                else:
                    worksheet.write(row, col, amount if amount > 0 else '', right)
            col += 1
            # worksheet.merge_range(row, col, row, col + 1, registration_fee if registration_fee > 0 else '', right)
            worksheet.write(row, col, '      ', right)
            worksheet.write(row, col + 1, '      ', right)
            worksheet.write(row, col + 2, '      ', right)
            worksheet.write(row, col + 3, '      ', right)
            worksheet.write(row, col + 4,
                            sum(each.fee_line.mapped('amount')), right)
            val['total'] += sum(each.fee_line.mapped('amount'))

            #    Other Collections
        # row += 1
        col = 0
        # other_fee_collections = self.env['fee.collection'].search(
        #     [('payment_date', '>=', invoices.from_date), ('payment_date', '<=', invoices.to_date),
        #      ('fee_type', '=', 'other'), ('state', '=', 'paid')])
        other_fee_collections = self.env['fee.collection'].search(
            [('payment_date', '=', invoices.to_date),
             ('fee_type', '=', 'other'), ('state', '=', 'paid')], order='id ASC')
        for each in other_fee_collections:
            row += 1
            worksheet.write(row, 0, str(each.payment_date.strftime('%d/%m/%Y')), center)
            worksheet.write(row, 1, each.paid_by if each.paid_by else '', left)
            worksheet.merge_range(row, 2, row, 5, each.purpose if each.purpose else '', left)
            worksheet.merge_range(row, 6, row, 8, '', boldc)
            col = 9
            for fee_item in self.env['fees.item'].search(
                    [('payable', '=', 'Government'),
                     ('is_other_fee', '=', False),
                     ('name', 'not in', ['Tuition Fee', 'Late Fee', 'Readmission Fee', 'Fine'])],
                    order='sort_order ASC'):
                worksheet.write(row, col, '', boldr)
                if fee_item.name == 'Registration Fee':
                    worksheet.write(row, col + 1, '', boldr)
                    col += 1
                col += 1
            col += 1
            other_collections = self.env['fees.item'].search([('is_other_fee', '=', True),
                                                              ('name', 'in',
                                                               ['Audit Objection', 'Tender Form', 'Other'])]).mapped(
                'id')
            other_collection_amount = sum(
                each.fee_line.filtered(lambda x: x.fee_id.id in other_collections).mapped('amount'))
            val['other_col'] += other_collection_amount
            other_library = self.env['fees.item'].search([('is_other_fee', '=', True),
                                                          ('name', '=', 'Other Library')]).mapped('id')
            other_library_amount = sum(
                each.fee_line.filtered(lambda x: x.fee_id.id in other_library).mapped('amount'))
            val['other_lib'] += other_library_amount
            other_laboratory = self.env['fees.item'].search([('is_other_fee', '=', True),
                                                             ('name', '=', 'Laboratory')]).mapped('id')
            other_laboratory_amount = sum(
                each.fee_line.filtered(lambda x: x.fee_id.id in other_laboratory).mapped('amount'))
            val['other_lab'] += other_laboratory_amount
            other_physical = self.env['fees.item'].search([('is_other_fee', '=', True),
                                                           ('name', '=', 'Physical Education')]).mapped('id')
            other_physical_amount = sum(
                each.fee_line.filtered(lambda x: x.fee_id.id in other_physical).mapped('amount'))
            val['other_phy'] += other_physical_amount
            other_total = other_collection_amount + other_library_amount + other_laboratory_amount + other_physical_amount
            val['total'] += other_total
            worksheet.write(row, col, other_collection_amount if other_collection_amount > 0 else '',
                            right)
            worksheet.write(row, col + 1, other_library_amount if other_library_amount > 0 else '',
                            right)
            worksheet.write(row, col + 2,
                            other_laboratory_amount if other_laboratory_amount > 0 else '', right)
            worksheet.write(row, col + 3, other_physical_amount if other_physical_amount > 0 else '',
                            right)
            worksheet.write(row, col + 4, other_total, right)
        row += 1

        # Calculation of Column wise total
        worksheet.merge_range(row, 0, row, 5, 'Total', boldc)
        worksheet.write(row, 6, val['tuition'] if val['tuition'] > 0 else '',
                        boldr)
        worksheet.write(row, 7, val['fine'] if val['fine'] > 0 else '', boldr)
        worksheet.write(row, 8, val['late_fee'] if val['late_fee'] > 0 else '', boldr)
        worksheet.write(row, 9, val['readmission'] if val['readmission'] > 0 else '', boldr)
        col = 9
        for fee_item in self.env['fees.item'].search(
                [('payable', '=', 'Government'),
                 ('is_other_fee', '=', False),
                 ('name', 'not in', ['Tuition Fee', 'Late Fee', 'Readmission Fee', 'Fine'])],
                order='sort_order ASC'):
            col += 1
            if fee_item.name == 'Registration Fee':
                worksheet.write(row, col, val['gov_reg'] if val['gov_reg'] > 0 else '', boldr)
                worksheet.write(row, col + 1, val['spl_reg'] if val['spl_reg'] > 0 else '', boldr)
                col += 1
            else:
                worksheet.write(row, col, val['fee_%d' % fee_item.id], boldr)
        col += 1
        worksheet.write(row, col, val['other_col'] if val['other_col'] > 0 else '',
                        boldr)
        worksheet.write(row, col + 1, val['other_lib'] if val['other_lib'] > 0 else '', boldr)
        worksheet.write(row, col + 2, val['other_lab'] if val['other_lab'] > 0 else '', boldr)
        worksheet.write(row, col + 3, val['other_phy'] if val['other_phy'] > 0 else '', boldr)
        worksheet.write(row, col + 4, val['total'] if val['total'] > 0 else '', boldr)

        # Headwise Collection Overview

        # fee_groups = student_fee_collections.mapped('fee_line.fee_id.group_id')
        # fee_groups = fee_groups + other_fee_collections.mapped('fee_line.fee_id.group_id')
        # fee_collections = student_fee_collections.mapped('fee_line')
        # fee_collections = fee_collections + other_fee_collections.mapped('fee_line')
        # row += 2
        # for each in fee_groups.sorted(key=lambda x: x.sort_order):
        #     row += 1
        #     worksheet.write(row, 0, each.name, left)
        #     if each.name == 'Registration Fee':
        #         worksheet.write(row, 1, val['gov_reg'] if val['gov_reg'] > 0 else 0, right)
        #     elif each.name == 'Special Fee':
        #         special_fee = sum(
        #             fee_collections.filtered(lambda x: x.fee_id.fee_group_id.id == each.id).mapped('amount')) + val[
        #                           'spl_reg']
        #         worksheet.write(row, 1, special_fee if special_fee > 0 else 0, right)
        #     else:
        #         worksheet.write(row, 1, sum(
        #             fee_collections.filtered(lambda x: x.fee_id.fee_group_id.id == each.id).mapped('amount')), right)
        # worksheet.write(row + 1, 0, 'Total', boldl)
        # worksheet.write(row + 1, 1, sum(fee_collections.mapped('amount')), boldr)

        fee_groups = student_fee_collections.mapped('fee_line.fee_id')
        fee_groups = fee_groups + other_fee_collections.mapped('fee_line.fee_id')
        fee_collections = student_fee_collections.mapped('fee_line')
        fee_collections = fee_collections + other_fee_collections.mapped('fee_line')
        row += 2
        special_fee_group = self.env['fees.group'].search([('name', '=', 'Special Fee')])
        for each in fee_groups.filtered(lambda x: x.group_id.name != 'Special Fee').sorted(key=lambda x: x.sort_order):
            row += 1
            worksheet.write(row, 0, each.name, left)
            if each.name == 'Registration Fee':
                worksheet.write(row, 1, val['gov_reg'] if val['gov_reg'] > 0 else 0, right)
            else:
                worksheet.write(row, 1, sum(
                    fee_collections.filtered(lambda x: x.fee_id.id == each.id).mapped('amount')), right)
        special_fee = sum(
            fee_collections.filtered(lambda x: x.fee_id.group_id.id == special_fee_group.id).mapped('amount')) + val[
                          'spl_reg']
        if special_fee > 0:
            worksheet.write(row + 1, 0, 'Special Fee', left)
            worksheet.write(row + 1, 1, special_fee if special_fee > 0 else 0, right)
        worksheet.write(row + 2, 0, 'Total', boldl)
        worksheet.write(row + 2, 1, sum(fee_collections.mapped('amount')), boldr)
        # sum(fee_collections.filtered(lambda x: x.fee_id.fee_group_id.id == each.id).mapped('amount'))

        # Remittance Report

        # row += 3
        # if invoices.from_date != invoices.to_date:
        #     remittance_val = {'spl_reg': 0, 'gov_reg': 0, 'reg_tot': 0, 'gov_reg_tot': 0, 'special_tot': 0,
        #                       'all_tot': 0}
        #     fee_groups = self.env['fees.item'].search([('payable', '=', 'Government'), ('group_id.name', '!=', 'Special Fee')], order='sort_order')
        #     special_fee_group = self.env['fees.group'].search([('name', '=', 'Special Fee')])
        #     worksheet.merge_range(row, 0, row, len(fee_groups),
        #                           'Details of Remittance on %s' % str(invoices.to_date.strftime('%d/%m/%Y')), boldc)
        #     row += 1
        #     # fee_groups = self.env['fees.group'].search([('fee_type_id.name', '=', 'Government')])
        #     middle_query = []
        #     for each in fee_groups:
        #         middle_query.append(
        #             """ SUM(CASE WHEN fi.id = """ + str(each.id) + """ THEN gfcl.amount ELSE 0 END) AS fee_""" + str(
        #                 each.id) + """ """)
        #     middle_query.append(""" SUM(CASE WHEN fi.id = """ + str(each.id) + """THEN gfcl.amount ELSE 0 END) AS
        #     fee_""" + str(each.id) + """ """)
        #     first_query = """ SELECT fc.payment_date, """
        #     middle_query = ','.join(middle_query) + ','
        #     last_query = """ SUM(gfcl.amount) AS total FROM fee_collection_line gfcl
        #                     INNER JOIN fee_collection fc ON fc.id = gfcl.fee_collection_id
        #                     INNER JOIN fees_item fi ON fi.id = gfcl.fee_id
        #                     WHERE fc.payment_date BETWEEN '%s' AND '%s' and state = 'post'
        #                     GROUP BY fc.payment_date ORDER BY fc.payment_date ASC """
        #     query = str(first_query) + str(middle_query) + str(last_query)
        #     self.env.cr.execute(query % (invoices.from_date, invoices.to_date - timedelta(days=1)))
        #     fee_groups = self.env.cr.dictfetchall()
        #     col = 0
        #     worksheet.write(row, col, 'Date', center)
        #     # val = {'all_tot': 0}
        #     for fee_group in self.env['fees.item'].search([('payable', '=', 'Government')]):
        #         col += 1
        #         remittance_val['fee_%d' % fee_group.id] = 0
        #         worksheet.write(row, col, fee_group.name, center)
        #     worksheet.write(row, col + 1, 'Total', center)
        #     for each in fee_groups:
        #         remittance_val['reg_tot'] = 0
        #         # special_fee = 0
        #         registration_fee = self.env['fees.item'].search([('name', '=', 'Registration Fee')])
        #         remittance_val['reg_tot'] = each['fee_%d' % registration_fee.id]
        #         gov_query = """ SELECT fc.payment_date,SUM(CASE WHEN fi.id = %s THEN 25 ELSE 0 END) AS gov_reg
        #                                                 FROM fee_collection_line gfcl
        #                                                 INNER JOIN fee_collection fc ON fc.id = gfcl.fee_collection_id
        #                                                 INNER JOIN fees_item fi ON fi.id = gfcl.fee_id
        #                                                 WHERE fc.payment_date BETWEEN '%s' and '%s' and state = 'post'
        #                                                 GROUP BY fc.payment_date ORDER BY fc.payment_date ASC  """
        #         self.env.cr.execute(gov_query % (registration_fee.id, invoices.from_date, invoices.to_date))
        #         gov_regs = self.env.cr.dictfetchall()
        #         res = {}
        #         for gov_reg in gov_regs:
        #             if gov_reg['payment_date'] == each['payment_date']:
        #                 res = gov_reg
        #                 break
        #         remittance_val['gov_reg'] = res['gov_reg']
        #         col = 0
        #         row += 1
        #         worksheet.write(row, col, str(each['payment_date'].strftime('%d/%m/%Y')), center)
        #         for fee in self.env['fees.item'].search([('payable', '=', 'Government')]):
        #             col += 1
        #             if fee.name == 'Registration Fee':
        #                 # for gov_reg in gov_regs:
        #                 worksheet.write(row, col, remittance_val['gov_reg'], right)
        #                 remittance_val['gov_reg_tot'] += remittance_val['gov_reg']
        #                 # remittance_val['reg_tot'] = each['fee_%d' % fee.id]
        #             elif fee.name == 'Special Fee':
        #                 special_fee = each['fee_%d' % fee.id] + (remittance_val['reg_tot'] - remittance_val['gov_reg'])
        #                 worksheet.write(row, col, special_fee, right)
        #                 remittance_val['special_tot'] += special_fee
        #             else:
        #                 remittance_val['fee_%d' % fee.id] += each['fee_%d' % fee.id]
        #                 worksheet.write(row, col, each['fee_%d' % fee.id], right)
        #         worksheet.write(row, col + 1, each['total'], right)
        #         remittance_val['all_tot'] += each['total']
        #     col = 0
        #     worksheet.write(row + 1, col, 'Total', boldc)
        #     for fee_group in self.env['fees.item'].search([('payable', '=', 'Government')]):
        #         col += 1
        #         if fee_group.name == 'Registration Fee':
        #             worksheet.write(row + 1, col, remittance_val['gov_reg_tot'], boldr)
        #         elif fee_group.name == 'Special Fee':
        #             worksheet.write(row + 1, col, remittance_val['special_tot'], boldr)
        #         else:
        #             worksheet.write(row + 1, col, remittance_val['fee_%d' % fee_group.id], boldr)
        #     worksheet.write(row + 1, col + 1, remittance_val['all_tot'], boldr)


class DFCRSelfFinanceXlsx(models.AbstractModel):
    _name = 'report.safi_students.dfcr_self_finance_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("DFCR")

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

        row = 3
        new_row = row + 1
        length = len(self.env['fees.item'].search([('is_other_fee', '!=', True)]))
        worksheet.merge_range(0, 0, 1, length + 5, self.env.user.company_id.name, boldc)
        if invoices.report_type == 'collection':
            worksheet.merge_range(2, 0, 2, length + 5, 'DAILY FEE COLLECTION REGISTER', boldc)

            worksheet.merge_range(row, 0, row + 7, 0, 'Date', boldc)
            worksheet.write(row + 8, 0, '1', boldc)
            worksheet.merge_range(row, 1, row + 7, 1, 'Name of the student', boldc)
            worksheet.write(row + 8, 1, '2', boldc)
            worksheet.merge_range(row, 2, row + 7, 2, 'admission Number', boldc)
            worksheet.write(row + 8, 2, '3', boldc)
            worksheet.merge_range(row, 3, row + 7, 3, 'Class', vertcal_align)
            worksheet.write(row + 8, 3, '4', boldc)
            worksheet.merge_range(row, 4, row + 7, 4, 'Receipt\nNo.', vertcal_align)
            worksheet.write(row + 8, 4, '5', boldc)
            worksheet.merge_range(row, 5, row + 7, 5, 'Receipt\nMode', vertcal_align)
            worksheet.write(row + 8, 5, '6', boldc)
            col = 5
            val = {
                'tuition': 0,
                'late_fee': 0,
                'readmission': 0,
                'fine': 0,
                'total': 0,
                'other_col': 0,
                'other_lib': 0,
                'other_lab': 0,
                'other_phy': 0,
                'other_tot': 0,
                'gov_reg': 0,
                'spl_reg': 0,
                'registration_fee': 0,

            }
            i = 5
            for fee_item in self.env['fees.item'].search([('is_other_fee', '=', False)], order='sort_order ASC'):
                col += 1
                i += 1
                val['fee_%d' % fee_item.id] = 0
                worksheet.merge_range(row, col, row + 7, col, '\n'.join(fee_item.name.split(' ')), vertcal_align)
                worksheet.write(row + 8, col, i, boldc)
            col += 1
            i += 1
            worksheet.merge_range(row, col, row + 7, col, 'Total', boldc)
            worksheet.write(row + 8, col, i, boldc)
            row = 11
            i = 0
            if invoices.receipt_mode:
                student_fee_collections = self.env['fee.collection'].search(
                    [('payment_date', '<=', invoices.to_date), ('payment_date', '>=', invoices.from_date),
                     ('fee_type', '=', 'student'), ('state', '=', 'paid'), ('receipt_mode', '=', invoices.receipt_mode)],
                    order='payment_date ASC')
            else:
                student_fee_collections = self.env['fee.collection'].search(
                    [('payment_date', '<=', invoices.to_date), ('payment_date', '>=', invoices.from_date),
                     ('fee_type', '=', 'student'), ('state', '=', 'paid')], order='payment_date ASC')
            header_list = []
            end = (len(student_fee_collections) // 30) + 1
            for j in range(1, end):
                header_list.append(j * 30)
            for each in student_fee_collections:
                i += 1
                row += 1
                worksheet.write(row, 0, str(each.payment_date.strftime('%d/%m/%Y')), center)
                worksheet.write(row, 1, each.student_id.name if each.student_id else each.paid_by, left)
                worksheet.write(row, 2, each.student_id.admission_number if each.student_id.admission_number else '', left)
                worksheet.write(row, 3, str(each.year) + ', ' + str(each.batch_id.complete_name), left)
                worksheet.write(row, 4, each.name, left)
                worksheet.write(row, 5, each.receipt_mode, left)
                col = 5
                for fee_item in self.env['fees.item'].search([('is_other_fee', '=', False)], order='sort_order ASC'):
                    col += 1
                    amount = sum(each.fee_line.filtered(lambda x: x.fee_id.id == fee_item.id).mapped('amount'))
                    val['fee_%d' % fee_item.id] += amount
                    worksheet.write(row, col, amount if amount > 0 else '', right)
                col += 1
                worksheet.write(row, col, sum(each.fee_line.mapped('amount')), right)
                val['total'] += sum(each.fee_line.mapped('amount'))
            row += 1
            # Calculation of Column wise total
            worksheet.merge_range(row, 0, row, 4, 'Total', boldc)
            col = 5
            for fee_item in self.env['fees.item'].search([('is_other_fee', '=', False)], order='sort_order ASC'):
                col += 1
                worksheet.write(row, col, val['fee_%d' % fee_item.id], boldr)
            col += 1
            worksheet.write(row, col, val['total'] if val['total'] > 0 else '', boldr)

        #         Refund register
        if invoices.report_type == 'refund':
            refund_row = 2
            worksheet.merge_range(refund_row, 0, refund_row, length + 5, 'DAILY FEE REFUND REGISTER', boldc)
            row = refund_row + 1
            worksheet.merge_range(row, 0, row + 7, 0, 'Date', boldc)
            worksheet.write(row + 8, 0, '1', boldc)
            worksheet.merge_range(row, 1, row + 7, 1, 'Name of the student', boldc)
            worksheet.write(row + 8, 1, '2', boldc)
            worksheet.merge_range(row, 2, row + 7, 2, 'Admission Number', boldc)
            worksheet.write(row + 8, 1, '3', boldc)
            worksheet.merge_range(row, 3, row + 7, 3, 'Class', vertcal_align)
            worksheet.write(row + 8, 2, '4', boldc)
            worksheet.merge_range(row, 4, row + 7, 4, 'Refund\nNo.', vertcal_align)
            worksheet.write(row + 8, 3, '5', boldc)
            worksheet.merge_range(row, 5, row + 7, 5, 'Refund\nMode', vertcal_align)
            worksheet.write(row + 8, 5, '6', boldc)
            col = 5
            val = {
                'tuition': 0,
                'late_fee': 0,
                'readmission': 0,
                'fine': 0,
                'total': 0,
                'other_col': 0,
                'other_lib': 0,
                'other_lab': 0,
                'other_phy': 0,
                'other_tot': 0,
                'gov_reg': 0,
                'spl_reg': 0,
                'registration_fee': 0,

            }
            i = 5
            for fee_item in self.env['fees.item'].search([('is_other_fee', '=', False)], order='sort_order ASC'):
                col += 1
                i += 1
                val['fee_refund_%d' % fee_item.id] = 0
                worksheet.merge_range(row, col, row + 7, col, '\n'.join(fee_item.name.split(' ')), vertcal_align)
                worksheet.write(row + 8, col, i, boldc)
            col += 1
            i += 1
            worksheet.merge_range(row, col, row + 7, col, 'Total', boldc)
            worksheet.write(row + 8, col, i, boldc)
            row = row + 8
            i = 0
            if invoices.receipt_mode:
                student_fee_refunds = self.env['fee.refund'].search(
                    [('refund_date', '<=', invoices.to_date), ('refund_date', '>=', invoices.from_date),
                     ('state', '=', 'refund'), ('payment_mode', '=', invoices.receipt_mode)], order='id ASC')
            else:
                student_fee_refunds = self.env['fee.refund'].search(
                    [('refund_date', '<=', invoices.to_date), ('refund_date', '>=', invoices.from_date),
                     ('state', '=', 'refund')], order='id ASC')
            header_list = []
            end = (len(student_fee_refunds) // 30) + 1
            for j in range(1, end):
                header_list.append(j * 30)
            for each in student_fee_refunds:
                i += 1
                row += 1
                worksheet.write(row, 0, str(each.refund_date.strftime('%d/%m/%Y')), center)
                worksheet.write(row, 1, each.student_id.name if each.student_id else '', left)
                worksheet.write(row, 2, each.student_id.admission_number if each.student_id.admission_number else '', left)
                worksheet.write(row, 3, str(each.fee_collection_id.year) + ', ' + str(each.batch_id.complete_name), left)
                worksheet.write(row, 4, each.name, left)
                worksheet.write(row, 5, each.payment_mode if each.payment_mode else '', left)
                col = 5
                for fee_item in self.env['fees.item'].search([('is_other_fee', '=', False)], order='sort_order ASC'):
                    col += 1
                    refund_amount = each.refund_line.filtered(lambda x: x.fee_id.id == fee_item.id).refund_amount
                    val['fee_refund_%d' % fee_item.id] += refund_amount
                    worksheet.write(row, col, refund_amount if refund_amount > 0 else '', right)
                col += 1
                worksheet.write(row, col, sum(each.refund_line.mapped('refund_amount')), right)
                val['total'] += sum(each.refund_line.mapped('refund_amount'))
            row += 1
            # Calculation of Column wise total
            worksheet.merge_range(row, 0, row, 3, 'Total', boldc)
            col = 5
            for fee_item in self.env['fees.item'].search([('is_other_fee', '=', False)], order='sort_order ASC'):
                col += 1
                worksheet.write(row, col, val['fee_refund_%d' % fee_item.id], boldr)
            col += 1
            worksheet.write(row, col, val['total'] if val['total'] > 0 else '', boldr)
