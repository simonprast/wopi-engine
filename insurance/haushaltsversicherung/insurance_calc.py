import json
import os
import re


def calc_insurance(insurance_vars, insurance_fields, do_calculate, submission_obj):
    dirname = os.path.dirname(__file__)
    vars_file = os.path.join(dirname, insurance_vars)
    # fields_file = os.path.join(dirname, insurance_fields)

    json_vars = open(vars_file, 'r')
    # json_fields = open(fields_file, 'r')

    v = json.loads(json_vars.read())
    # f = json.loads(json_fields.read())

    p = re.compile('(?<!\\\\)\'')
    json_data_string = p.sub('\"', submission_obj.data)

    submission_data = json.loads(json_data_string)

    values = {}

    c = submission_data

    # n = loop index, i = current field, c = submission_data
    # c and f can both be used here, as both require all fields currently
    # see required tag at submission.insurancesubmission.api.dev.serializers
    for n, i in enumerate(c):
        fc = c[n]['field_content']
        var_name = i['field_name']
        if var_name in v:
            var_value = v[var_name]
            if fc in var_value or str(fc) in var_value:
                var_value = var_value[str(fc)]
        else:
            var_value = submission_data[n]['field_content']
            if var_value in v:
                var_value = v[var_value]

        values.update({var_name: var_value})

    # print(values)

    price = do_calculate(values, v)

    return price
