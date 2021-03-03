from insurance.insurance_calc import c


def do_calculate(vl, v):
    if c(vl, 'vs', 0) != 0:
        vs = c(vl, 'vs', 0)
    else:
        vs = vl['groesse'] * v['pauschalwert_qm']

    price = vs * v['praemiensatz']
    price = price + price / \
        v['praemiensatz'] * \
        c(vl, 'hochwasser', v['hochwasser']["1"])

    # Sicherungen vorhanden
    if c(vl, 'alarmanlage', 1) != 1 or c(vl, 'sicherheitstuer', 1) != 1 or c(vl, 'extrasecurity', 1) != 1:
        # Nicht ständig bewohnt
        if c(vl, 'staendigbewohnt', 1) != 1:
            # Nicht im Ortsgebiet
            if c(vl, 'ortsgebiet', 1) != 1:
                price = price * 2
    else:  # Keine Sicherungen vorhanden
        if c(vl, 'staendigbewohnt', 1) != 1:
            if c(vl, 'ortsgebiet', 1) != 1:
                price = price * 2.5

    # Auf Glasbruch verzichten
    price = price * c(vl, 'glas', 1)

    # Zweitwohnsitz ODER Einpersonenhaushalt
    price = price * c(vl, 'zweitein', 1)

    # Wenn Alarmanlage oder andere Sicherheitstechnik vorhanden wird Rabatt abgezogen
    if c(vl, 'alarmanlage', 1) != 1 or c(vl, 'sicherheitstuer', 1) != 1 or c(vl, 'extrasecurity', 1) != 1:
        price = price * c(vl, 'alarmanlage', 1)

    # Extra Rabatt für Smart Home Security
    price = price * c(vl, 'smarthomesecurity', 1)

    # Treuebonus, unveränderbar
    price = price * 0.9

    # Regionalrabatt je Bundesland
    price = price * c(vl, 'regionalrabatt', 1)

    # Aufpreis für kürzere Laufzeit
    price = price * c(vl, 'shortterm', 1)

    # Rabatt für Selbstbehaltsanteil
    price = price * c(vl, 'selbstbehaltsnachlass', 1)

    # SPARDA-Bonus, unveränderbar
    price = price * 0.55
    return price, vs
