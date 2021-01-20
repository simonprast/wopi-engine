from insurance.insurance_calc import c


def do_calculate(vl, v):
    if c(vl, 'vs', 0) != 0:
        vs = c(vl, 'vs', 0)
    else:
        vs = vl['groesse'] * v['pauschalwert_m2']

    price = vs * v['praemiensatz']
    price = price + price / \
        v['praemiensatz'] * \
        c(vl, 'hochwasser', v['hochwasser']['a'])
    price = price * c(vl, 'staendigbewohnt', 1)
    price = price * c(vl, 'glas', 1)
    price = price * c(vl, 'zweitein', 1)
    if c(vl, 'alarmanlage', 1) != 1 or c(vl, 'extrasecurity', 1) != 1:
        price = price * c(vl, 'alarmanlage', 1)
    price = price * c(vl, 'smarthomesecurity', 1)
    price = price * 0.9  # Treuebonus
    price = price * c(vl, 'regionalrabatt', 1)
    price = price * c(vl, 'shortterm', 1)
    price = price * c(vl, 'selbstbehaltsnachlass', 1)
    price = price * 0.55  # SPARDA-Bonus
    return price, vs
