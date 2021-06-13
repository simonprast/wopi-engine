import json
import os
# import re


def calc_insurance(insurance_vars, insurance_fields, insurance_meta, do_calculate, submission_data):
    dirname = os.path.dirname(__file__)
    vars_file = os.path.join(dirname, insurance_vars)
    meta_file = os.path.join(dirname, insurance_meta)
    # fields_file = os.path.join(dirname, insurance_fields)

    json_vars = open(vars_file, 'r')
    json_meta = open(meta_file, 'r')
    # json_fields = open(fields_file, 'r')

    v = json.loads(json_vars.read())
    meta = json.loads(json_meta.read())
    # f = json.loads(json_fields.read())

    # This part is replacing the single-quotes of a invalid json string with double-quotes.
    # This is only needed if a submission object is used for calculation instead of a live-submission.
    # p = re.compile('(?<!\\\\)\'')
    # json_data_string = p.sub('\"', submission_obj.data)
    # submission_data = json.loads(json_data_string)

    values = {}

    c = submission_data

    # This for-loop uses the submission data, and either adds it to the
    # values dict or gets a value out of the variables-dictionary 'v'.
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

    price, vs = do_calculate(values, v)

    return_dict = meta
    return_dict.update({
        "price": price,
        "vs": vs
    })

    return return_dict
    # return price, meta


# Checking the dictionary value for a KeyError, and if
# the value is not available, return a given default value.
# This is used within the X_calc.py files.
def c(dict, key, default):
    try:
        var = dict[key]
        return var
    except KeyError:
        return default
