import io
import json
import xlsxwriter
from odoo import fields, models
from odoo.tools import date_utils


class StockValuationReport(models.TransientModel):
    """ Wizard for printing stock valuation report.We will get both excl
        and pdf reports"""
    _name = "stock.valuation.report"
    _description = "Stock Valuation Report"

    product_id = fields.Many2one('product.product', 
                                 string='Product',
                                 help='Select product\nPilih produk')
    product_category_id = fields.Many2one('product.category',
                                          string='Product Category', 
                                          required=True,
                                          help='Select product category\nPilih kategori produk')
    from_Date = fields.Datetime(string='From Date', required=True,
                                default=fields.Datetime.now(),
                                help='Start from date?')
    to_date = fields.Datetime(string='To Date', required=True,
                              default=fields.Datetime.now(),
                              help='Until date?')
    company_id = fields.Many2one('res.company',
                                 string="Company",
                                 help="Select company\nPilih perusahaan",
                                 default=lambda self: self.env.company)

    def action_print_pdf_report(self):
        """ Function to print pdf report.Passing data to pdf template"""
        lang = f"'{self.env.context['lang']}'"

        # membentuk Query SQL rekursif untuk mendapatkan seluruh kategori produk dan subkategori yang terkait.
        query = """ WITH RECURSIVE CategoryHierarchy AS ( 
                        SELECT id,name,parent_id 
                        FROM product_category 
                        WHERE id = {} 
                        UNION ALL 
                        SELECT c.id, c.name, c.parent_id 
                        FROM product_category c
                        JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                    )
                    SELECT 
                        CategoryHierarchy.id as category_id, 
                        CategoryHierarchy.name as category_name,
                        stock_valuation_layer.create_date, 
                        product_template.name->>{} as name, 
                        stock_valuation_layer.description, 
                        product_category.complete_name,res_company.name as company_name, 
                        quantity, 
                        stock_valuation_layer.unit_cost, 
                    value FROM CategoryHierarchy JOIN product_category on 
                    CategoryHierarchy.id = product_category.id JOIN 
                    product_template on product_category.id = 
                    product_template.categ_id JOIN product_product on 
                    product_template.id = product_product.product_tmpl_id JOIN
                        stock_valuation_layer on product_product.id = 
                        stock_valuation_layer.product_id JOIN res_company on 
                        stock_valuation_layer.company_id = res_company.id
                    """.format(self.product_category_id.id, lang)
        
        # Mendapatkan ID produk, ID lokasi, ID perusahaan, tanggal mulai, dan tanggal akhir
        product_id = self.product_id.id
        company_id = self.company_id.id
        from_date = self.from_Date
        to_date = self.to_date

        # jika parameter self.product_id dan self.company_id tidak kosong
        if self.product_id and self.company_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.company_id ='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, 
                    product_id, 
                    company_id,
                    from_date,
                    to_date))
            
        # jika parameter self.product_id tidak kosong
        elif self.product_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, 
                    product_id, 
                    from_date, 
                    to_date))
            
        # jika parameter self.company_id tidak kosong
        elif self.company_id:
            self.env.cr.execute(
                """{} where stock_valuation_layer.company_id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, 
                    company_id, 
                    from_date, 
                    to_date))
            
        # jika semua kondisi diatas tidak terpenuhi
        else:
            self.env.cr.execute("""{}""".format(query))

        # Mengambil semua hasil dari query dalam bentuk dictionary
        stock_valuation = self.env.cr.dictfetchall()

        # membentuk data yang akan diteruskan ke laporan excel
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_valuation': stock_valuation
        }

        # menghasilkan action laporan PDF menggunakan referensi stock_valuation_report
        return self.env.ref(
            'stock_card_trisakti.stock_valuation_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file"""
        lang = f"'{self.env.context['lang']}'"

        # membentuk Query SQL rekursif untuk mendapatkan seluruh kategori produk dan subkategori yang terkait.
        query = """ WITH RECURSIVE CategoryHierarchy AS ( 
                        SELECT id,name,parent_id 
                        FROM product_category 
                        WHERE id = {} 
                        UNION ALL 
                        SELECT c.id, c.name, c.parent_id 
                        FROM product_category c
                        JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                    )
                    SELECT 
                        CategoryHierarchy.id as category_id, 
                        CategoryHierarchy.name as category_name,
                        stock_valuation_layer.create_date, 
                        product_template.name->>{} as name, 
                        stock_valuation_layer.description, 
                        product_category.complete_name,res_company.name as company_name, 
                        quantity, 
                        stock_valuation_layer.unit_cost, 
                    value FROM CategoryHierarchy JOIN product_category on 
                    CategoryHierarchy.id = product_category.id JOIN 
                    product_template on product_category.id = 
                    product_template.categ_id JOIN product_product on 
                    product_template.id = product_product.product_tmpl_id JOIN
                        stock_valuation_layer on product_product.id = 
                        stock_valuation_layer.product_id JOIN res_company on 
                        stock_valuation_layer.company_id = res_company.id
                    """.format(self.product_category_id.id, lang)
        
        # Mendapatkan ID produk, ID lokasi, ID perusahaan, tanggal mulai, dan tanggal akhir
        product_id = self.product_id.id
        company_id = self.company_id.id
        from_date = self.from_Date
        to_date = self.to_date

        # jika parameter self.product_id dan self.company_id tidak kosong
        if self.product_id and self.company_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.company_id ='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, 
                    product_id, 
                    company_id,
                    from_date,
                    to_date))
            
        # jika parameter self.product_id tidak kosong
        elif self.product_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, 
                    product_id, 
                    from_date, 
                    to_date))
            
        # jika parameter self.company_id tidak kosong
        elif self.company_id:
            self.env.cr.execute(
                """{} where stock_valuation_layer.company_id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, 
                    company_id, 
                    from_date, 
                    to_date))
            
        # jika semua kondisi diatas tidak terpenuhi
        else:
            self.env.cr.execute("""{}""".format(query))
        
        # Mengambil semua hasil dari query dalam bentuk dictionary
        stock_valuation = self.env.cr.dictfetchall()

        # membentuk data yang akan diteruskan ke laporan excel    
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_valuation': stock_valuation
        }

        # menghasilkan action laporan excel menggunakan referensi stock_valuation_report
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.valuation.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Stock valuation report'}}

    def get_xlsx_report(self, data, response):
        """ Function to print excel report.Customizing excel file and added data
            :param data :Dictionary contains results
            :param response : Response from the controller"""
        output = io.BytesIO()

        # membuat workbook baru dan menambahkan worksheet baru di dalamnya
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()

        # Membuat Format untuk Header dan Teks:
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center'})
        
        # mengatur lebar kolom 
        sheet.set_column(0, 10, 24)

        # Menulis Header dan Informasi Perusahaan:
        sheet.merge_range('C2:E3', 'STOCK VALUATION REPORT', head)
        sheet.merge_range('C4:E4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Date', txt)
        sheet.write('C8', 'Product Name', txt)
        sheet.write('D8', 'Description', txt)
        sheet.write('E8', 'Product Category', txt)
        sheet.write('F8', 'Company Name', txt)
        sheet.write('G8', 'Quantity', txt)
        sheet.write('H8', 'Unit Cost', txt)
        sheet.write('I8', 'Value', txt)

        # menulis data produk pada sheet
        records = data['stock_valuation']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['create_date'], txt)
            sheet.write(row, 2, record['name'], txt)
            sheet.write(row, 3, record['description'], txt)
            sheet.write(row, 4, record['complete_name'], txt)
            sheet.write(row, 5, record['company_name'], txt)
            sheet.write(row, 6, record['quantity'], txt)
            sheet.write(row, 7, record['unit_cost'], txt)
            sheet.write(row, 8, record['value'], txt)
            flag += 1
            row += 1
        workbook.close()

        # mengirimkan file excel sebagai respon
        output.seek(0)
        response.stream.write(output.read())
        output.close()
