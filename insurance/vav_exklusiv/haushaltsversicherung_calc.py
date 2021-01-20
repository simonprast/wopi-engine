from insurance.insurance_calc import c


def do_calculate(vl, v):
    if c(vl, 'vs', 0) != 0:
        vs = c(vl, 'vs', 0)
        custom_vs = True
    else:
        vs = vl['groesse'] * v['pauschalwert_m2']
        custom_vs = False

    price = vs / 1000 * v['clusterfaktor']
    price = price * c(vl, 'staendigbewohnt', 1)
    if custom_vs:
        price = price * 1.1
    price = price * v['policy']['exklusiv']
    price = price * c(vl, 'publicworker', 1)
    price = price * c(vl, 'mehrspartenbonus', 1)
    price = price * 0.85  # VAV Bonus
    price = price * c(vl, 'alarmanlage', 1)
    price = price * c(vl, 'extrasecurity', 1)
    price = price * c(vl, 'selbstbehaltsnachlass', 1)
    price = price * c(vl, 'shortterm', 1)
    price = price * 0.9  # Vertriebsonus
    return price, vs
