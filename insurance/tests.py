import json
import re

from django.test import TestCase

from insurance.insurance_calc import calc_insurance
from insurance.haushaltsversicherung.haushaltsversicherung_calc import do_calculate

from submission.insurancesubmission.models import InsuranceSubmission


class CalculationTestCase(TestCase):
    def setUp(self):

        data_d = [
            {
                'field_name': 'groesse',
                'field_title': 'Wohnungsgröße',
                'field_content': 66
            },
            {
                'field_name': 'hochwasser',
                'field_title': 'Hochwasserschutz',
                'field_content': 'b2'
            },
            {
                'field_name': 'staendigbewohnt',
                'field_title': 'Wohnung in nicht ständig bewohnten Gebäuden außerhalb des Ortsgebiets?',
                'field_content': 2
            },
            {
                'field_name': 'glas',
                'field_title': 'Auf Glasbruch verzichten',
                'field_content': 1
            },
            {
                'field_name': 'zweitein',
                'field_title': 'Zweitwohnsitz oder Einpersonenhaushalt',
                'field_content': 1
            },
            {
                'field_name': 'regionalrabatt',
                'field_title': 'Regionalrabatt',
                'field_content': 'kaernten'
            },
            {
                'field_name': 'selbstbehaltsnachlass',
                'field_title': 'Selbstbehaltsnachlass',
                'field_content': 200
            }

        ]

        InsuranceSubmission.objects.create(data=data_d)

    def test_calculate(self):
        submission_obj = InsuranceSubmission.objects.get(pk=1)

        p = re.compile('(?<!\\\\)\'')
        json_data_string = p.sub('\"', submission_obj.data)
        submission_data = json.loads(json_data_string)

        price = calc_insurance('haushaltsversicherung/haushaltsversicherung_vars.json',
                               'haushaltsversicherung/haushaltsversicherung_fields.json',
                               'haushaltsversicherung/haushaltsversicherung_meta.json',
                               do_calculate,
                               submission_data)
        print(price)
