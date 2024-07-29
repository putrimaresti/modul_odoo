import io
import json
import xlsxwriter
from odoo import fields, models, api
from odoo.tools import date_utils
from odoo.exceptions import ValidationError


class StockProductReport(models.TransientModel):
    """ Wizard for printing product report.Both excel and pdf can be print
        by filtering the data """
    _name = "stock.product.report"
    _description = "Stock Product Report"

    product_id = fields.Many2one('product.product', 
                                 string="Product",
                                 help='Select product\nPilih produk')
    product_category_id = fields.Many2one('product.category', required=True,
                                          string="Product Category",
                                          help="Select stock location\nPilih lokasi stok")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='To pick the company')
    from_date = fields.Datetime(string="Date from",
                                help='Stock move start from')
    to_date = fields.Datetime(string='To date', 
                              help='Stock move end')
            
    def action_print_pdf_report(self):
        """ Function to print pdf report passing value to the pdf report"""
        lang = f"'{self.env.context['lang']}'"

        # membentuk query SQL rekursif untuk mendapatkan hirarki kategori produk
        query = """WITH RECURSIVE CategoryHierarchy AS (
                    SELECT id,name,parent_id
                    FROM product_category 
                    WHERE id = {} 
                    UNION ALL 
                    SELECT c.id, c.name, c.parent_id 
                    FROM product_category c 
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                ) 
                SELECT CategoryHierarchy.id as category_id,
                    CategoryHierarchy.name as category_name,
                    product_template.name->>{} as product_name,
                    product_product.qty_available,
                    product_product.free_qty,
                    product_product.incoming_qty,
                    product_product.outgoing_qty 
                FROM CategoryHierarchy
                JOIN product_category on CategoryHierarchy.id = product_category.id
                JOIN product_template on product_category.id = product_template.categ_id
                JOIN product_product on product_template.id = product_product.product_tmpl_id""".format(
                    self.product_category_id.id, lang)
        
        # mendapatkan ID produk
        product_id = self.product_id.id
        # jika ada produk spesifik yang dipilih, tambahkan kondisi pada query
        if self.product_id:
            self.env.cr.execute(
                """{} and product_product.id = '{}' """.format(
                    query, 
                    product_id))
            
        # jika tidak ada produk spesifik, jalankan query asli
        else:
            self.env.cr.execute("""{}""".format(query))

        # Mengambil semua hasil dari query dalam bentuk dictionary
        stock_product = self.env.cr.dictfetchall()

        # membentuk data yang akan diteruskan ke laporan PDF
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_product': stock_product
        }

        # menghasilkan action laporan PDF menggunakan referensi pada stock_product_report
        return self.env.ref(
            'stock_card_trisakti.stock_product_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ function to pass data to Excel report"""
        lang = f"'{self.env.context['lang']}'"

        # membentuk query SQL rekursif untuk mendapatkan hirarki kategori produk
        query = """WITH RECURSIVE CategoryHierarchy AS (
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
                    product_template.name->>{} as product_name,
                    product_product.qty_available,
                    product_product.free_qty,
                    product_product.incoming_qty,
                    product_product.outgoing_qty
                FROM CategoryHierarchy
                JOIN product_category on CategoryHierarchy.id = product_category.id
                JOIN product_template on product_category.id = product_template.categ_id
                JOIN product_product on product_template.id = product_product.product_tmpl_id""".format(
            self.product_category_id.id, lang)
        
        # mendapatkan ID produk
        product_id = self.product_id.id

        # jika ada produk spesifik yang dipilih, tambahkan kondisi pada query
        if self.product_id:
            self.env.cr.execute(
                """{} and product_product.id = '{}' """.format(
                    query, 
                    product_id))
            
        # Jika tidak ada produk spesifik, jalankan query asli
        else:
            self.env.cr.execute("""{}""".format(query))

        # Mengambil semua hasil dari query dalam bentuk dictionary
        stock_product = self.env.cr.dictfetchall()

        # membentuk data yang akan diteruskan ke laporan XLX
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_product': stock_product,
        }

        # Mengembalikan aksi untuk menghasilkan laporan dalam format Excel dengan data yang telah disusun.
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.product.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Stock Product Report'}}

    def get_xlsx_report(self, data, response):
        """ function to print Excel report and customising the Excel file
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
        sheet.set_column(0, 8, 24)

        # Menulis Header dan Informasi Perusahaan:
        sheet.merge_range('B2:D3', 'STOCK REPORT', head)
        sheet.merge_range('B4:D4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Product Name', txt)
        sheet.write('C8', 'Product Category', txt)
        sheet.write('D8', 'On Hand Quantity', txt)
        sheet.write('E8', 'Quantity Unreserved', txt)
        sheet.write('F8', 'Incoming Quantity', txt)
        sheet.write('G8', 'Outgoing Quantity', txt)

        # menulis data produk pada sheet
        records = data['stock_product']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['product_name'], txt)
            sheet.write(row, 2, record['category_name'], txt)
            sheet.write(row, 3, record['qty_available'], txt)
            sheet.write(row, 4, record['free_qty'], txt)
            sheet.write(row, 5, record['incoming_qty'], txt)
            sheet.write(row, 6, record['outgoing_qty'], txt)
            flag += 1
            row += 1
        workbook.close()

        # mengirimkan file excel sebagai respon
        output.seek(0)
        response.stream.write(output.read())
        output.close()
