from fraser import (Sats, Verbfras, Nominalfras, Adjektivfras, Infinitivfras,
                    Adverbfras, Bisatsfras, Prepositionsfras, Mening, Samordningsled,
                    Frågepronomensfras, Frågadverbfras, Negationsadverbfras)
from ordklasser import Substantiv, Pronomen, Subjunktion, Preposition, Konjunktion, Interrogativdeterminant
from ordbokläsare import hämta_lexem_id, hämta_form, kolla_lexems_egenskap
from bitflaggor import Species, Grad, Kasus, Personlighet, Person, Numerus, Tempus


def rendera(indata, språk: str = 'sv') -> str:
    if isinstance(indata, Mening):
        return rendera_mening(indata, språk)
    return rendera_sats(indata, språk)  # bakåtkompatibilitet: ensam Sats


def rendera_mening(mening: Mening, språk: str) -> str:
    delar = _bygg_sats(mening.huvud, språk)
    for led in mening.samordningar:
        konj_lexem_id = hämta_lexem_id(led.konjunktion.koncept_id, språk)
        delar.append(hämta_form(konj_lexem_id))
        delar.extend(_bygg_sats(led.sats, språk))
    text = " ".join(delar)
    # Sista satsen avgör skiljetecken
    sista_sats = mening.samordningar[-1].sats if mening.samordningar else mening.huvud
    tecken = "?" if _är_fråga(sista_sats) else "."
    return text[0].upper() + text[1:] + tecken


def rendera_sats(sats: Sats, språk: str) -> str:
    mening = " ".join(_bygg_sats(sats, språk))
    tecken = "?" if _är_fråga(sats) else "."
    return mening[0].upper() + mening[1:] + tecken


def _är_fråga(sats: Sats) -> bool:
    """Avgör om satsen är en fråga — ja/nej-flagga eller interrogativt led."""
    if sats.ja_nej_fråga:
        return True
    vf = sats.predikatfras
    if vf:
        for fras in [vf.subjektfras, vf.direktobjektfras, vf.indirektobjektfras]:
            if isinstance(fras, Frågepronomensfras):
                return True
            if isinstance(fras, Nominalfras) and isinstance(getattr(fras, 'determinant', None), Interrogativdeterminant):
                return True
    for adv in sats.adverbial:
        if isinstance(adv, Frågadverbfras):
            return True
    return False


def _bygg_sats(sats: Sats, språk: str) -> list[str]:
    """Bygger upp satsens ord som lista — utan versal och punkt.

    Hantering av frågeordföljd:
    1. Ja/nej-fråga (inga frågeord) → V-S-inversion
    2. Exakt ett frågeord i subjektposition → normal V2-ordföljd
    3. Exakt ett frågeord i icke-subjektposition → fronta + V-S-inversion
    4. Flera frågeord → naturlig ordföljd (ingen frontering)
    """
    vf = sats.predikatfras

    # ── Fas 1: rendera varje del med etikett ──────────────────────────────
    # Varje post: (etikett, text, fras) — fras behövs för språkspecifik efterbehandling
    märkta = []

    if vf.subjektfras:
        fras = vf.subjektfras
        if isinstance(fras, Frågepronomensfras):
            märkta.append(('fråga_subjekt', _rendera_komplement(fras, språk), fras))
        elif isinstance(fras, Nominalfras) and isinstance(getattr(fras, 'determinant', None), Interrogativdeterminant):
            märkta.append(('fråga_subjekt', _rendera_komplement(fras, språk), fras))
        else:
            märkta.append(('subjekt', _rendera_komplement(fras, språk), fras))
    elif vf.verb:
        # Opersonligt verb utan subjektfras → dummy-subjekt ("det" / "il")
        verb_lexem_id = hämta_lexem_id(vf.verb.koncept_id, språk)
        pers = int(kolla_lexems_egenskap(verb_lexem_id, 'personlighet') or 0)
        if pers & int(Personlighet.OPERSONLIG):
            dummy = 'det' if språk == 'sv' else 'il'
            märkta.append(('subjekt', dummy, None))

    if vf.verb:
        verb_text = rendera_verb(vf, språk)
        verb_delar = verb_text.split(' ', 1)
        if len(verb_delar) > 1:
            märkta.append(('verb', verb_delar[0], None))
            märkta.append(('verb_particip', verb_delar[1], None))
        else:
            märkta.append(('verb', verb_text, None))

    # Ordföljd: svenska IO före DO, franska DO före IO
    if språk == 'sv':
        objekt_par = [(vf.indirektobjektfras, 'io'), (vf.direktobjektfras, 'do')]
    else:
        objekt_par = [(vf.direktobjektfras, 'do'), (vf.indirektobjektfras, 'io')]

    for fras, namn in objekt_par:
        if fras:
            if isinstance(fras, Frågepronomensfras):
                märkta.append(('fråga_objekt', _rendera_komplement(fras, språk), fras))
            elif isinstance(fras, Nominalfras) and isinstance(getattr(fras, 'determinant', None), Interrogativdeterminant):
                märkta.append(('fråga_objekt', _rendera_komplement(fras, språk), fras))
            else:
                märkta.append(('objekt', _rendera_komplement(fras, språk), fras))

    for adv in _sortera_adverbial(sats.adverbial, språk):
        if isinstance(adv, Frågadverbfras):
            märkta.append(('fråga_adverbial', _rendera_komplement(adv, språk), adv))
        elif isinstance(adv, Negationsadverbfras):
            märkta.append(('negationsadverb', _rendera_komplement(adv, språk), adv))
        else:
            märkta.append(('adverbial', _rendera_komplement(adv, språk), adv))

    # ── Fas 2: räkna frågeord och tillämpa ordföljd ───────────────────────
    fråge_etiketter = [e for e, _, _ in märkta if e.startswith('fråga_')]
    antal_frågeord = len(fråge_etiketter)

    if sats.ja_nej_fråga and antal_frågeord == 0:
        # V-S-inversion: byt plats på subjekt och verb
        subj_idx = next((i for i, (e, _, _) in enumerate(märkta) if e == 'subjekt'), None)
        verb_idx = next((i for i, (e, _, _) in enumerate(märkta) if e == 'verb'), None)
        if subj_idx is not None and verb_idx is not None and subj_idx < verb_idx:
            märkta[subj_idx], märkta[verb_idx] = märkta[verb_idx], märkta[subj_idx]

    elif antal_frågeord == 1 and 'fråga_subjekt' not in fråge_etiketter:
        # Fronta det enda frågeordet + V-S-inversion
        fråge_idx = next(i for i, (e, _, _) in enumerate(märkta) if e.startswith('fråga_'))
        fråga = märkta.pop(fråge_idx)

        # V-S-inversion på det som återstår
        subj_idx = next((i for i, (e, _, _) in enumerate(märkta) if e in ('subjekt',)), None)
        verb_idx = next((i for i, (e, _, _) in enumerate(märkta) if e == 'verb'), None)
        if subj_idx is not None and verb_idx is not None and subj_idx < verb_idx:
            märkta[subj_idx], märkta[verb_idx] = märkta[verb_idx], märkta[subj_idx]

        märkta.insert(0, fråga)

    # Flera frågeord (antal_frågeord > 1) eller fråga_subjekt ensamt → naturlig ordföljd

    # ── Fas 3: negation + språkspecifik efterbehandling ───────────────────
    har_negationsadverb = any(e == 'negationsadverb' for e, _, _ in märkta)
    if språk == 'sv':
        if sats.negation or har_negationsadverb:
            märkta = _svensk_negation(märkta, sats)
    elif språk == 'fr':
        märkta = _fransk_satsbehandling(märkta, sats)

    return [text for _, text, _ in märkta]


def _svensk_negation(märkta: list, sats: Sats) -> list:
    """Placerar negationspartikeln korrekt i svenska satser.

    Partikeln är antingen 'inte' (sats.negation=True) eller ett negationsadverb
    (t.ex. 'aldrig', 'inte längre') som hämtas ur märkta-listan.

    Huvudsats:  S V NEG (particip) O   /  V S NEG (particip) O  (inversion)
    Bisats:     S NEG V (particip) O
    """
    är_bisats = isinstance(getattr(sats, 'förälder', None), Bisatsfras)

    # Hämta negationspartikeln: negationsadverb har företräde över 'inte'
    neg_idx = next((i for i, (e, _, _) in enumerate(märkta) if e == 'negationsadverb'), None)
    if neg_idx is not None:
        neg_post = märkta.pop(neg_idx)
    else:
        neg_post = ('negation', 'inte', None)

    # Verb-index kan ha förskjutits efter pop
    verb_idx = next((i for i, (e, _, _) in enumerate(märkta) if e == 'verb'), None)
    if verb_idx is None:
        return märkta

    if är_bisats:
        märkta.insert(verb_idx, neg_post)
    else:
        insert_pos = verb_idx + 1
        if insert_pos < len(märkta) and märkta[insert_pos][0] == 'subjekt':
            insert_pos += 1
        märkta.insert(insert_pos, neg_post)

    return märkta


def _fransk_satsbehandling(märkta: list, sats: Sats) -> list:
    """Fransk efterbehandling av satsordföljd efter fas 2.

    1. V-S-inversion med bindestreck: verb + pronomensubjekt → "mange-t-il"
       Euphoniskt -t- inskjuts när verbet slutar på vokal och pronomenet börjar på vokal.
       För sammansatta tempus inverteras bara hjälpverbet: "a mangé" + "il" → "a-t-il mangé".

    2. Negation: ne...pas omsluter det finita verbet.
       Enkelt tempus: "ne mange pas" / "ne mange-t-il pas"
       Sammansatt:    "n'a pas (mangé)" / "n'a-t-il pas (mangé)"

    3. que → quoi: franskt "que" (what) i icke-fronterad position blir "quoi"
       (klitisk/tonisk alternering styrd av syntaktisk position).
    """
    # 1. V-S-inversion med bindestreck
    i = 0
    while i < len(märkta) - 1:
        etikett_v, text_v, fras_v = märkta[i]
        etikett_s, text_s, fras_s = märkta[i + 1]
        if etikett_v == 'verb' and etikett_s == 'subjekt':
            if isinstance(fras_s, Nominalfras) and isinstance(fras_s.huvuddel, Pronomen):
                sammanslagen = _fransk_inversion(text_v, text_s)
                märkta[i] = (etikett_v, sammanslagen, fras_v)
                märkta.pop(i + 1)
                continue  # hoppa inte framåt — listan har krympt
        i += 1

    # 2. Negation: ne…X  (X = 'pas', eller ett negationsadverb som 'jamais', 'plus' …)
    neg_adv_idx = next((i for i, (e, _, _) in enumerate(märkta) if e == 'negationsadverb'), None)
    if sats.negation or neg_adv_idx is not None:
        # Bestäm negationspartikeln
        if neg_adv_idx is not None:
            neg_text = märkta[neg_adv_idx][1]
            märkta.pop(neg_adv_idx)
        else:
            neg_text = 'pas'

        verb_idx = next((i for i, (e, _, _) in enumerate(märkta) if e == 'verb'), None)
        if verb_idx is not None:
            etikett, verb_text, fras = märkta[verb_idx]
            vokaler = 'aeéèêëiïoôuùûyæœà'
            if verb_text[0].lower() in vokaler:
                ny_text = f"n'{verb_text}"
            else:
                ny_text = f"ne {verb_text}"
            märkta[verb_idx] = (etikett, ny_text, fras)
            märkta.insert(verb_idx + 1, ('negation', neg_text, None))

    # 3. que → quoi i icke-fronterad position
    for i, (etikett, text, fras) in enumerate(märkta):
        if (etikett.startswith('fråga_') and etikett != 'fråga_subjekt'
                and isinstance(fras, Frågepronomensfras)
                and text == 'que' and i > 0):
            märkta[i] = (etikett, 'quoi', fras)

    return märkta


def _fransk_inversion(verb_text: str, subj_text: str) -> str:
    """Skapar fransk V-S-inversion med bindestreck och eufoniskt -t-.

    Sammansatta tempus: "a mangé" + "il" → "a-t-il mangé"
    (bara hjälpverbet inverteras).
    """
    delar = verb_text.split(' ', 1)
    aux = delar[0]
    particip = delar[1] if len(delar) > 1 else None

    vokaler = 'aeéèêëiïoôuùûyæœà'
    if aux[-1].lower() in vokaler and subj_text[0].lower() in vokaler:
        inverterad = f"{aux}-t-{subj_text}"
    else:
        inverterad = f"{aux}-{subj_text}"

    if particip:
        return f"{inverterad} {particip}"
    return inverterad


def _sortera_adverbial(adverbial: list, språk: str) -> list:
    """Bisatsfras sist i SVO-språk (tyngdprincipen). Annars bevaras användarens ordning."""
    SVO_SPRÅK = {'sv', 'fr', 'de', 'en'}
    if språk not in SVO_SPRÅK:
        return adverbial
    return sorted(adverbial, key=lambda f: isinstance(f, Bisatsfras))


def _rendera_komplement(fras, språk: str) -> str:
    if isinstance(fras, Nominalfras):
        return rendera_nominalfras(fras, språk)
    if isinstance(fras, Infinitivfras):
        return rendera_infinitivfras(fras, språk)
    if isinstance(fras, Bisatsfras):
        return rendera_bisatsfras(fras, språk)
    if isinstance(fras, Prepositionsfras):
        return rendera_prepositionsfras(fras, språk)
    if isinstance(fras, Adverbfras):
        return rendera_adverbfras(fras, språk)
    if isinstance(fras, Frågepronomensfras):
        return rendera_frågepronomensfras(fras, språk)
    if isinstance(fras, Frågadverbfras):
        return rendera_frågadverbfras(fras, språk)
    if isinstance(fras, Negationsadverbfras):
        return rendera_negationsadverbfras(fras, språk)
    raise TypeError(f"Okänd frastyp: {type(fras)}")


def rendera_infinitivfras(inf: Infinitivfras, språk: str) -> str:
    inre_sats = inf.sats
    vf        = inre_sats.predikatfras
    lexem_id  = hämta_lexem_id(vf.verb.koncept_id, språk)
    verb_form = hämta_form(lexem_id, tempus=Tempus.INFINITIV)

    # Separera negationsadverb från övriga adverbial
    neg_adv = next((adv for adv in inre_sats.adverbial if isinstance(adv, Negationsadverbfras)), None)
    övriga  = [adv for adv in inre_sats.adverbial if adv is not neg_adv]

    delar = [verb_form]
    for adv in _sortera_adverbial(övriga, språk):
        delar.append(_rendera_komplement(adv, språk))
    verb_del = " ".join(delar)

    if språk == 'sv':
        if neg_adv:
            neg_text = rendera_negationsadverbfras(neg_adv, språk)
            return f"att {neg_text} {verb_del}"
        if inre_sats.negation:
            return f"att inte {verb_del}"
        return f"att {verb_del}"

    # Franska: ne X + infinitiv (både ne och X går före vid infinitiv)
    if neg_adv:
        neg_text = rendera_negationsadverbfras(neg_adv, språk)
        return f"ne {neg_text} {verb_del}"
    if inre_sats.negation:
        return f"ne pas {verb_del}"
    return verb_del


def rendera_bisatsfras(bf: Bisatsfras, språk: str) -> str:
    delar = []
    if bf.inledare:
        lexem_id = hämta_lexem_id(bf.inledare.koncept_id, språk)
        delar.append(hämta_form(lexem_id))
    if bf.sats:
        delar.extend(_bygg_sats(bf.sats, språk))
    return " ".join(delar)


def rendera_prepositionsfras(pf: Prepositionsfras, språk: str) -> str:
    prep_form = None
    if pf.preposition:
        lexem_id = hämta_lexem_id(pf.preposition.koncept_id, språk)
        prep_form = hämta_form(lexem_id)

    komplement = None
    if pf.komplementfras:
        komplement = _rendera_komplement(pf.komplementfras, språk)

    # Franska obligatoriska kontraktioner: à + le → au, à + les → aux,
    # de + le → du, de + les → des
    if språk == 'fr' and prep_form and komplement:
        kontraherad = _fransk_kontraktion(prep_form, komplement)
        if kontraherad:
            return kontraherad

    delar = []
    if prep_form:
        delar.append(prep_form)
    if komplement:
        delar.append(komplement)
    return " ".join(delar)


def _fransk_kontraktion(preposition: str, komplement: str) -> str | None:
    """Hanterar obligatoriska franska kontraktioner av preposition + bestämd artikel.

    à + le → au,   à + les → aux    (à + la oförändrad)
    de + le → du,  de + les → des   (de + la oförändrad)
    """
    ord = komplement.split(' ', 1)
    artikel = ord[0]
    rest = ord[1] if len(ord) > 1 else None

    kontraktioner = {
        ('à', 'le'): 'au',
        ('à', 'les'): 'aux',
        ('de', 'le'): 'du',
        ('de', 'les'): 'des',
    }

    kontraherad = kontraktioner.get((preposition, artikel))
    if kontraherad:
        return f"{kontraherad} {rest}" if rest else kontraherad
    return None


def rendera_adverbfras(af: Adverbfras, språk: str) -> str:
    lexem_id = hämta_lexem_id(af.adverb.koncept_id, språk)
    return hämta_form(lexem_id)


def rendera_frågepronomensfras(fps: Frågepronomensfras, språk: str) -> str:
    lexem_id = hämta_lexem_id(fps.frågepronomen.koncept_id, språk)
    return hämta_form(lexem_id, kasus=fps.kasus)


def rendera_frågadverbfras(faf: Frågadverbfras, språk: str) -> str:
    lexem_id = hämta_lexem_id(faf.frågadverb.koncept_id, språk)
    return hämta_form(lexem_id)


def rendera_negationsadverbfras(naf: Negationsadverbfras, språk: str) -> str:
    lexem_id = hämta_lexem_id(naf.negationsadverb.koncept_id, språk)
    return hämta_form(lexem_id)


def _subjekts_kongruens(vf: Verbfras, språk: str) -> tuple[int, int]:
    """Returnerar (person, numerus) för verbets kongruens.

    Regler:
    1. Opersonligt verb  → alltid person=3, numerus=1 (t.ex. regna/pleuvoir)
    2. Pronomen-subjekt  → person och numerus hämtas från Lexem (inneboende egenskap)
    3. Substantiv-subjekt → person=3, numerus från nominalfrasen
    4. Inget subjekt     → fel — ger ett tydligt undantag
    """
    verb_lexem_id = hämta_lexem_id(vf.verb.koncept_id, språk)
    personlighet  = kolla_lexems_egenskap(verb_lexem_id, 'personlighet') or 0

    if int(personlighet) & int(Personlighet.OPERSONLIG):
        return Person.TREDJE, Numerus.SINGULAR

    if vf.subjektfras is None:
        raise ValueError(f"Personligt verb saknar subjekt: koncept_id={vf.verb.koncept_id}")

    # Frågepronomen som subjekt → tredje person singular ("Vem springer?")
    if isinstance(vf.subjektfras, Frågepronomensfras):
        return Person.TREDJE, Numerus.SINGULAR

    nf = vf.subjektfras

    if isinstance(nf.huvuddel, Pronomen):
        lexem_id = hämta_lexem_id(nf.huvuddel.koncept_id, språk)
        person  = kolla_lexems_egenskap(lexem_id, 'person')
        numerus = kolla_lexems_egenskap(lexem_id, 'numerus')
        return Person(int(person)), Numerus(int(numerus))

    if isinstance(nf.huvuddel, Substantiv):
        return Person.TREDJE, Numerus(int(nf.numerus))

    raise ValueError(f"Okänd subjektstyp: {type(nf.huvuddel)}")


def rendera_verb(vf: Verbfras, språk: str) -> str:
    lexem_id        = hämta_lexem_id(vf.verb.koncept_id, språk)
    person, numerus = _subjekts_kongruens(vf, språk)
    if språk == 'sv':
        return hämta_form(lexem_id, tempus=vf.tempus)
    return hämta_form(lexem_id, tempus=vf.tempus, person=person, numerus=numerus)


def rendera_nominalfras(nf: Nominalfras, språk: str) -> str:
    lexem_id = hämta_lexem_id(nf.huvuddel.koncept_id, språk)

    # Svenska böjer substantivet i species; franska hanterar bestämdhet via artikel
    species_arg = nf.species if språk == 'sv' else None

    substantiv_form = hämta_form(
        lexem_id,
        numerus = nf.numerus,
        species = species_arg,
        kasus   = nf.kasus,
    )

    har_attribut = nf.attribut is not None
    är_räknebar = kolla_lexems_egenskap(lexem_id, 'räknebar')
    oräknebar = är_räknebar is not None and int(är_räknebar) == 0

    # Oräkneliga substantiv renderas alltid i singular
    if oräknebar:
        substantiv_form = hämta_form(lexem_id, numerus=Numerus.SINGULAR,
                                     species=species_arg, kasus=nf.kasus)

    # Artikel — interrogativ determinant ersätter vanlig artikel
    artikel = None
    if isinstance(nf.determinant, Interrogativdeterminant):
        det_lexem_id = hämta_lexem_id(nf.determinant.koncept_id, språk)
        noun_genus = kolla_lexems_egenskap(lexem_id, 'genus')
        artikel = hämta_form(det_lexem_id, numerus=nf.numerus, genus=noun_genus)
    elif isinstance(nf.huvuddel, Substantiv):
        if nf.species == Species.OBESTAMD:
            # Oräkneliga substantiv tar ingen obestämd artikel ("mat" inte "en mat")
            artikel = None if oräknebar else _artikel_obestamd(lexem_id, nf.numerus, språk)
        elif nf.species == Species.BESTAMD:
            artikel = _artikel_bestamd(lexem_id, nf.numerus, språk,
                                       har_attribut=har_attribut, kasus=nf.kasus)

    # Adjektiv — behöver substantivets genus för kongruens
    adj_form      = None
    adj_prenominal = True
    if nf.attribut:
        noun_genus = kolla_lexems_egenskap(lexem_id, 'genus')
        adj_form, adj_prenominal = rendera_adjektivfras(
            nf.attribut, noun_genus, nf.numerus, nf.species, språk
        )

    # Fransk elision: le/la → l' framför vokal/stumt h
    if språk == 'fr' and artikel in ('le', 'la'):
        nästa = adj_form if (adj_form and adj_prenominal) else substantiv_form
        if nästa and nästa[0].lower() in 'aeéèêëiïoôuùûyæœàâ':
            artikel = "l'"

    # Sätt ihop: [artikel] [adj (pre)] [substantiv] [adj (post)]
    delar = []
    if artikel:
        # Elided artikel (l') klistras ihop med nästa ord
        if isinstance(artikel, str) and artikel.endswith("'"):
            nästa = adj_form if (adj_form and adj_prenominal) else substantiv_form
            delar.append(f"{artikel}{nästa}")
            # Markera att nästa redan inkluderades
            if adj_form and adj_prenominal:
                adj_form = None
            else:
                substantiv_form = None
        else:
            delar.append(artikel)
    if adj_form and adj_prenominal:
        delar.append(adj_form)
    if substantiv_form:
        delar.append(substantiv_form)
    if adj_form and not adj_prenominal:
        delar.append(adj_form)

    return " ".join(delar)


def rendera_adjektivfras(af: Adjektivfras, genus: int, numerus, species, språk: str) -> tuple[str, bool]:
    """Returnerar (böjd adjektivform, prenominal).
    genus   = substantivets genus som int från Lexem
    numerus = från nominalfrasen
    species = från nominalfrasen (används i sv för adjektivkongruens)
    """
    lexem_id = hämta_lexem_id(af.adjektiv.koncept_id, språk)
    grad = af.grad or Grad.POSITIV

    species_arg = species if språk == 'sv' else None

    form = hämta_form(lexem_id, numerus=numerus, species=species_arg, genus=genus, grad=grad)

    prenominal_val = kolla_lexems_egenskap(lexem_id, 'prenominal')
    prenominal = bool(prenominal_val) if prenominal_val is not None else True

    return form, prenominal


def _artikel_obestamd(lexem_id: int, numerus, språk: str) -> str:
    genus = _genus(lexem_id)

    if språk == 'sv':
        if numerus == 2:
            return None
        return 'en' if genus == 1 else 'ett'

    if språk == 'fr':
        if numerus == 2:
            return 'des'
        return 'un' if genus == 1 else 'une'

    return None


def _artikel_bestamd(lexem_id: int, numerus, språk: str,
                     har_attribut: bool = False, kasus=None) -> str:
    """Returnerar bestämd artikel.

    Svenska: ingen prefix-artikel utan adjektiv; 'den/det/de' när adjektiv finns.
    Franska: alltid le/la/les, men dativ ger au/à la/aux.
    """
    if språk == 'sv':
        if not har_attribut:
            return None  # suffix på substantivet räcker
        genus = _genus(lexem_id)
        if numerus == 2:
            return 'de'
        return 'den' if genus == 1 else 'det'

    if språk == 'fr':
        genus = _genus(lexem_id)
        är_dativ = kasus is not None and (int(kasus) & int(Kasus.DATIV))
        if är_dativ:
            if numerus == 2:
                return 'aux'
            return 'au' if genus == 1 else 'à la'
        if numerus == 2:
            return 'les'
        return 'le' if genus == 1 else 'la'

    return None


def _genus(lexem_id: int) -> int | None:
    v = kolla_lexems_egenskap(lexem_id, 'genus')
    return int(v) if v is not None else None
