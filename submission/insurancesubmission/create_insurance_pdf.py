import json
import uuid
import os

from django.conf import settings
from django.utils.text import slugify

from fpdf import FPDF

from insurance.models import Insurance

from .models import Document


def create_pdf(request, submission):
    if request.user.is_anonymous:
        full_name = request.data.get('first_name') + ' ' + request.data.get('last_name')
    else:
        full_name = request.user.first_name + ' ' + request.user.last_name

    insurance = Insurance.objects.get(insurance_key=request.data.get('key'))
    fields = json.loads(insurance.insurance_fields)

    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 15)
    pdf.write(h=7, txt='Beratungsprotokoll - ' + insurance.insurance_name + '\n')

    pdf.set_font('Helvetica', '', 12)

    for field in fields:
        # print(field)
        # print(field['field_title'])
        pdf.set_font('Helvetica', 'B', 12)
        pdf.write(h=8, txt=field['field_title'] + '\n')
        pdf.set_font('Helvetica', '', 12)

        if field['field_name'] not in request.data:
            pdf.write(h=8, txt='Keine Angabe')

        elif field.get('options') and type(field.get('options')) is dict:
            translation = field['options'][str(request.data.get(field['field_name']))]
            pdf.write(h=8, txt=translation)

        else:
            pdf.write(h=8, txt=str(request.data.get(field['field_name'])))

        pdf.write(h=8, txt='\n\n')

        # print('\n')

    document = Document.objects.create(
        insurance_submission=submission,
        title='Beratungsprotokoll zur Haushaltsversicherung',
        description=full_name + " " + insurance.insurance_name,
        pos_x=0.7,
        pos_y=0.9
    )

    filename = slugify(full_name) + str(document.id) + '.pdf'
    folder = 'policy/' + str(uuid.uuid4())

    path = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(path)

    full_path = os.path.join(path, filename)
    pdf.output(full_path)
    document.template.name = folder + '/' + filename

    # Count pages of a PDF file
    pages = pdf.page_no()
    document.page_index = pages - 1

    document.save()
