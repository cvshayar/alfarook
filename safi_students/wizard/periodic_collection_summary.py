from odoo import fields, models, api


class PeriodicCollectionSummary(models.TransientModel):
    _name = 'periodic.collection.summary'
    _description = 'Periodic Collection Summary'

    from_date = fields.Date(default=fields.Date.today())
    to_date = fields.Date(default=fields.Date.today())
    fees_item_id = fields.Many2one('fees.item')
    batch_id = fields.Many2one('batch.batch')

    def print_excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', []), 'model': 'periodic.collection.summary', 'form': self.read()[0]}
        return self.env.ref('safi_students.periodic_collection_summary_xlsx_id').report_action(self, data=datas,
                                                                                               config=False)


class PeriodicCollectionSummaryXlsx(models.AbstractModel):
    _name = 'report.safi_students.periodic_collection_summary_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("Periodic Collection Summary")

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

        if invoices.batch_id and not invoices.fees_item_id:
            date_query = """ SELECT fc.payment_date FROM fee_collection fc
                            INNER JOIN batch_batch bb ON bb.id = fc.batch_id
                            WHERE fc.payment_date between %s and %s and fc.state in ('paid', 'post')
                            and fc.batch_id = %s
                            GROUP BY fc.payment_date """
            self.env.cr.execute(date_query, [invoices.from_date, invoices.to_date, invoices.batch_id.id])
        elif invoices.fees_item_id and not invoices.batch_id:
            date_query = """ SELECT fc.payment_date FROM fee_collection fc
                            INNER JOIN fee_collection_line fcl ON fcl.fee_collection_id = fc.id
                            INNER JOIN fees_item fi ON fi.id = fcl.fee_id
                            WHERE fc.payment_date between %s and %s and fc.state in ('paid', 'post')
                            and fcl.fee_id = %s
                            GROUP BY fc.payment_date """
            self.env.cr.execute(date_query, [invoices.from_date, invoices.to_date, invoices.fees_item_id.id])
        elif invoices.fees_item_id and invoices.batch_id:
            date_query = """ SELECT fc.payment_date FROM fee_collection fc
                            INNER JOIN fee_collection_line fcl ON fcl.fee_collection_id = fc.id
                            INNER JOIN batch_batch bb ON bb.id = fc.batch_id
                            INNER JOIN fees_item fi ON fi.id = fcl.fee_id
                            WHERE fc.payment_date between %s and %s and fc.state in ('paid', 'post')
                            and fc.batch_id = %s and fcl.fee_id = %s
                            GROUP BY fc.payment_date """
            self.env.cr.execute(date_query,
                                [invoices.from_date, invoices.to_date, invoices.batch_id.id, invoices.fees_item_id.id])
        else:
            date_query = """ SELECT fc.payment_date FROM fee_collection fc
                            WHERE fc.payment_date between %s and %s and fc.state in ('paid', 'post')
                            GROUP BY fc.payment_date """
            self.env.cr.execute(date_query, [invoices.from_date, invoices.to_date])
        payment_dates = self.env.cr.dictfetchall()
        sub_select_query = []
        select_query = """ SELECT fi.name as item, """
        header_col = 0
        header_row = 1
        date_column = {}
        worksheet.merge_range(header_row - 1, header_col, header_row - 1, len(payment_dates) + 1, self.env.company.name,
                              boldc)
        worksheet.write(header_row, header_col, 'ITEMS', boldc)
        for payment_date in payment_dates:
            header_col += 1
            worksheet.write(header_row, header_col, payment_date['payment_date'].strftime('%d/%m/%Y'), boldc)
            date_column.update({'d%s' % str(payment_date['payment_date']).replace('-', '_'): header_col})
            sub_select_query.append(""" SUM(CASE WHEN fc.payment_date = '""" + str(payment_date['payment_date']) + """' THEN fcl.amount
                ELSE 0 END) AS D""" + str(payment_date['payment_date']).replace('-', '_') + """ """)
        worksheet.write(header_row, header_col + 1, 'Total', boldc)
        date_column.update({'total': header_col + 1})
        if invoices.batch_id and not invoices.fees_item_id:
            from_query = """ SUM(fcl.amount) as total FROM fee_collection_line fcl 
                            INNER JOIN fee_collection fc ON fc.id = fcl.fee_collection_id
                            INNER JOIN fees_item fi ON fi.id = fcl.fee_id 
                            INNER JOIN batch_batch bb ON bb.id = fc.batch_id """
            where_query = """ WHERE fc.state in ('paid', 'post') AND fc.payment_date between %s and %s 
                            and fc.batch_id = %s GROUP BY fi.name """
        elif invoices.fees_item_id and not invoices.batch_id:
            from_query = """ SUM(fcl.amount) as total FROM fee_collection_line fcl 
                            INNER JOIN fee_collection fc ON fc.id = fcl.fee_collection_id
                            INNER JOIN fees_item fi ON fi.id = fcl.fee_id """
            where_query = """ WHERE fc.state in ('paid', 'post') AND fc.payment_date between %s and %s
                            and fcl.fee_id = %s GROUP BY fi.name """
        elif invoices.fees_item_id and invoices.batch_id:
            from_query = """ SUM(fcl.amount) as total FROM fee_collection_line fcl 
                            INNER JOIN fee_collection fc ON fc.id = fcl.fee_collection_id
                            INNER JOIN batch_batch bb ON bb.id = fc.batch_id
                            INNER JOIN fees_item fi ON fi.id = fcl.fee_id """
            where_query = """ WHERE fc.state in ('paid', 'post') AND fc.payment_date between %s and %s
                            and fcl.fee_id = %s and fc.batch_id = %s GROUP BY fi.name """
        else:
            from_query = """ SUM(fcl.amount) as total FROM fee_collection_line fcl 
                            INNER JOIN fee_collection fc ON fc.id = fcl.fee_collection_id
                            INNER JOIN fees_item fi ON fi.id = fcl.fee_id """
            where_query = """ WHERE fc.state in ('paid', 'post') AND fc.payment_date between %s and %s
                            GROUP BY fi.name """
        if sub_select_query:
            query = select_query + ','.join(sub_select_query) + ', ' + from_query + where_query
        else:
            query = select_query + from_query + where_query
        if invoices.batch_id and not invoices.fees_item_id:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, invoices.batch_id.id])
        elif invoices.fees_item_id and not invoices.batch_id:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, invoices.fees_item_id.id])
        elif invoices.batch_id and invoices.fees_item_id:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date, invoices.fees_item_id.id, invoices.batch_id.id])
        else:
            self.env.cr.execute(query, [invoices.from_date, invoices.to_date])
        item_collections = self.env.cr.dictfetchall()
        row = 2
        for item_collection in item_collections:
            dates = list(item_collection.keys())
            dates.remove('item')
            dates.remove('total')
            worksheet.write(row, 0, item_collection['item'], boldl)
            for date in dates:
                worksheet.write(row, date_column[date], item_collection[date], right)
            worksheet.write(row, date_column['total'], item_collection['total'], boldr)
            row += 1
