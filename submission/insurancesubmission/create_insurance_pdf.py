import json
import uuid
import os

from fpdf import FPDF

from francy import settings
from insurance.models import Insurance
from .models import Document


def create_pdf(request, submission):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.set_font('Helvetica', '', 15)

    pdf.add_page()

    insurance = Insurance.objects.get(insurance_key=request.data.get('key'))
    fields = json.loads(insurance.insurance_fields)

    for field in fields:
        pdf.write(h=8, txt=field.get('field_title') + '\n')
        if field.get('options'):
            for option in field.get('options'):
                if option == request.data.get(field.get('field_name')):
                    pdf.set_font('Helvetica', 'B', 15)
                pdf.write(h=8, txt=str(option) + " ")
                pdf.set_font('Helvetica', '', 15)
        else:
            pdf.write(h=8, txt=str(request.data.get(field.get('field_name'))))
        pdf.write(h=8, txt='\n')

    if request.user.is_anonymous:
        name = request.data.get('first_name') + request.data.get('last_name')
    else:
        name = request.user.first_name + request.user.last_name

    document = Document.objects.create(
        insurance_submission=submission,
        title=name + " pdf",
        description=name + " " + insurance.insurance_name
        )

    filename = name + str(document.id) + ".pdf"
    folder = 'policy/' + str(uuid.uuid4())
    path = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(path)

    path = os.path.join(path, filename)
    pdf.output(path)
    document.document.name = path
    document.save()
