import os
import PyPDF2
import uuid

from fpdf import FPDF


def insert_payment_data(document, data, coordinates):
    print(document.template.name)
    print(data)
    print(coordinates)

    pdf = FPDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(False)
    pdf.set_font('Arial', '', 15)

    pdf.add_page()

    for item in data:
        print(item)
        print(data[item])
        print(coordinates[item])
        pdf.set_xy(coordinates[item][0], coordinates[item][1])
        pdf.cell(0, 0, str(data[item]), 0, 0, 'L')

    pdf_location = 'pdfs/' + str(uuid.uuid4()) + '/'
    filename = 'template-data.pdf'
    os.makedirs('media/' + pdf_location)
    pdf.output('media/' + pdf_location + filename)

    input_file = 'media/' + document.template.name
    output_file = 'media/' + pdf_location + filename

    with open(input_file, 'rb') as template_file:
        template = PyPDF2.PdfFileReader(template_file)

        with open('media/' + pdf_location + filename, 'rb') as content_file:
            content = PyPDF2.PdfFileReader(content_file)

            template_page = template.getPage(0)

            content_page = content.getPage(0)

            template_page.mergePage(content_page)

            pdfWriter = PyPDF2.PdfFileWriter()

            pdfWriter.addPage(template_page)

            with open(output_file, 'wb') as final_file:
                pdfWriter.write(final_file)


def insert_signature(document, signature):
    print(document.document.name)
    pass
