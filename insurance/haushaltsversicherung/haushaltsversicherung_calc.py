from insurance.insurance_calc import c


def do_calculate(vl, v):
    price = vl['groesse'] * v['pauschalwert_m2'] * v['praemiensatz']
    price = price + price / \
        v['praemiensatz'] * \
        c(vl, 'hochwasser', v['hochwasser']['a'])
    price = price * c(vl, 'staendigbewohnt', 1)
    price = price * c(vl, 'glas', 1)
    price = price * c(vl, 'zweitein', 1)
    price = price * c(vl, 'regionalrabatt', 1)
    price = price * c(vl, 'selbstbehaltsnachlass', 1)
    return price
