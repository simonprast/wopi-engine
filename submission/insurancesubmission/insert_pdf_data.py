import os
import PyPDF2
import uuid

from django.core.files import File

from fpdf import FPDF


def insert_payment_data(document, data, coordinates):
    # Initialize the new PDF file containing custom data.
    pdf = create_pdf()

    pdf.set_font('Courier', '', 12.2)

    # Place the Text at the PDF file.
    for item in data:
        pdf.set_xy(coordinates[item][0], coordinates[item][1])

        if item == 'iban':
            pdf.set_font('Courier', '', 12.2)

        insert_text = str(data[item])

        if ('iban' in data and 'bic' in data) and (item == 'iban' or item == 'bic'):
            insert_text = insert_text.replace(' ', '')
            insert_text = '  '.join(insert_text)

        pdf.cell(0, 0, insert_text, 0, 0, 'L')

    # Merge the files, using the document (+ its template file) and the newly created data PDF.
    output_file = merge_files(document, pdf)

    # Create a file for the Django FileField
    document_file = open(output_file, 'rb')
    template_djangofile = File(document_file)
    document.template.save(document.title + '.pdf', template_djangofile)
    document_file.close()

    # Sign the document
    insert_signature(document)


def insert_signature(document):
    # Initialize the new PDF file containing custom data.
    pdf = create_pdf()

    # Place the signature file onto the data PDF file.
    pos_x_mm = pdf.w * document.pos_x
    pos_y_mm = pdf.h * document.pos_y

    pdf.set_xy(pos_x_mm, pos_y_mm)

    print('height:', document.signature.height)
    print('width:', document.signature.width)

    if document.signature.height > document.signature.width:
        pdf.image(document.signature.name, h=30)
    else:
        pdf.image(document.signature.name, w=40)

    # pdf.cell(0, 0, ' ', 0, 0, 'L')

    # Merge the files, using the document (+ its template file) and the newly created data PDF.
    output_file = merge_files(document, pdf, document.page_index)

    # Create a file for the Django FileField
    document_file = open(output_file, 'rb')
    template_djangofile = File(document_file)
    document.document.save(document.title + '.pdf', template_djangofile)
    document_file.close()


def create_pdf():
    pdf = FPDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(False)
    pdf.set_font('Helvetica', '', 15)

    pdf.add_page()

    return pdf


def create_filepaths(document, pdf):
    pdf_location = 'pdfs/' + str(uuid.uuid4()) + '/'
    filename = document.title + '.pdf'
    os.makedirs('media/' + pdf_location)
    pdf.output('media/' + pdf_location + filename + '.signature')
    pdf.close()

    input_file = 'media/' + document.template.name
    output_file = 'media/' + pdf_location + filename

    return input_file, output_file, pdf_location


def merge_files(document, pdf, index=0):
    if not index:
        index = 0

    input_file, output_file, pdf_location = create_filepaths(document, pdf)

    with open(input_file, 'rb') as template_file:
        template = PyPDF2.PdfFileReader(template_file)

        with open('media/' + pdf_location + document.title + '.pdf.signature', 'rb') as content_file:
            content = PyPDF2.PdfFileReader(content_file)

            template_page = template.getPage(index)
            content_page = content.getPage(0)

            template_page.mergePage(content_page)

            output = PyPDF2.PdfFileWriter()

            for i in range(template.getNumPages()):
                if i == index:
                    output.addPage(template_page)
                else:
                    page = template.getPage(i)
                    output.addPage(page)

            with open(output_file, 'wb') as final_file:
                output.write(final_file)

    return output_file
