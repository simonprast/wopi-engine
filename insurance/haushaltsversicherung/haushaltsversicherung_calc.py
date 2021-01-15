def do_calculate(vl, v):
    price = vl['groesse'] * v['pauschalwert_m2'] * v['praemiensatz_haushalt']
    price = price + price / v['praemiensatz_haushalt'] * vl['hochwasser']
    price = price * vl['staendigbewohnt']
    price = price * vl['glas']
    price = price * vl['zweitein']
    price = price * vl['regionalrabatt']
    price = price * vl['selbstbehaltsnachlass']
    return price
