from insurance.insurance_calc import c


def do_calculate(vl, v):
    groesse = vl['groesse']
    if groesse >= 0 and groesse < 60:
        groesse_faktor = v['groesse_faktor']['60']
    elif groesse < 120:
        groesse_faktor = v['groesse_faktor']['120']
    elif groesse < 180:
        groesse_faktor = v['groesse_faktor']['180']
    elif groesse < 250:
        groesse_faktor = v['groesse_faktor']['250']
    elif groesse >= 250:
        groesse_faktor = v['groesse_faktor']['251']

    alter = vl['alter']
    if alter >= 0 and alter < 45:
        alter_faktor = v['alter_faktor']['45']
    elif alter < 60:
        alter_faktor = v['alter_faktor']['60']
    elif alter >= 60:
        alter_faktor = v['alter_faktor']['61']

    faktor_ohne_kosten = v['tarifniveau'] * \
        vl['hhv_zonenfaktor'] * alter_faktor * groesse_faktor

    faktor_mit_kosten = faktor_ohne_kosten / (1 - v['kosten'])
    faktor_mit_steuer = faktor_mit_kosten * (1 + v['versicherungssteuer'])

    # faktor_netto = faktor_mit_kosten * (1 + v['zuschlag'])
    faktor_brutto = faktor_mit_steuer * (1 + v['zuschlag'])

    if c(vl, 'vs', 0) != 0:
        vs = c(vl, 'vs', 0)
        custom_vs = True
    else:
        vs = vl['groesse'] * v['pauschalwert_qm']
        custom_vs = False

    # Zuschlag zur Grundprämie bei individueller Versicherungssumme
    if custom_vs:
        clusterfaktor = faktor_mit_steuer * (1 + v['zuschlag'])
        price = vs / 1000 * \
            faktor_brutto * v['deckungsvariante']
    else:
        clusterfaktor = faktor_mit_steuer
        price = vs / 1000 * clusterfaktor * v['deckungsvariante']

    # price_zuschlag_netto = vs / 1000 * faktor_netto * v['deckungsvariante']
    # price_zuschlag_brutto = vs / 1000 * faktor_brutto * v['deckungsvariante']

    # Ist das Gebäude mehr als 9 Monate im Jahr bewohnt?
    price = price * vl['staendigbewohnt']

    # Schwimmbecken-Versicherung, Value 1 = Schwimmbecken, Value 2 = Schwimmbecken + Technik
    price = price + c(vl, 'schwimmbecken', 0)

    # Alarmanlage am Gebäude vorhanden?
    price = price * c(vl, 'alarmanlage', 1)

    # Sicherheitstüre vorhanden?
    price = price * c(vl, 'sicherheitstuer', 1)

    # Selbstbehaltsnachlass
    # 0 = kein SB und kein Nachlass
    # 1 = SB 100€ / 10% Nachlass
    # 2 = SB 300€ / 20% Nachlass
    # 3 = SB 500€ / 30% Nachlass
    price = price * c(vl, 'selbstbehaltsnachlass', 1)

    # Rabatt für aktive und im Ruhestand befindliche Angehörige des öffentlichen Dienstes
    # sowie deren im gemeinsamen Haushalt lebende Ehegatten oder Lebensgefährten
    price = price * c(vl, 'publicworker', 1)

    # Andere Versicherung bei VAV vorhanden?
    price = price * c(vl, 'mehrspartenbonus', 1)

    # Verkürzte Laufzeit
    # 0 = 10 Jahre Laufzeit
    # 1 = 5 Jahre Laufzeit
    # 2 = 3 Jahre Laufzeit
    price = price * c(vl, 'shortterm', 1)

    # VAV Bonus 15% flat
    price = price * 0.85

    # Vertriebsonus 10% flat
    price = price * 0.9

    # price = price * v['policy']['exklusiv']
    # price = price * c(vl, 'publicworker', 1)
    # price = price * c(vl, 'mehrspartenbonus', 1)
    # price = price * 0.85  # VAV Bonus
    # price = price * c(vl, 'alarmanlage', 1)
    # price = price * c(vl, 'extrasecurity', 1)
    # price = price * c(vl, 'selbstbehaltsnachlass', 1)
    # price = price * c(vl, 'shortterm', 1)
    # price = price * 0.9  # Vertriebsonus
    return price, vs
