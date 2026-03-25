from fraser import Sats, Verbfras, Nominalfras, Adjektivfras, Infinitivfras, Adverbfras, Bisatsfras, Prepositionsfras, Mening, Samordningsled
from ordklasser import Substantiv, Pronomen, Subjunktion, Preposition, Konjunktion
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
    return text[0].upper() + text[1:] + "."


def rendera_sats(sats: Sats, språk: str) -> str:
    mening = " ".join(_bygg_sats(sats, språk))
    return mening[0].upper() + mening[1:] + "."


def _bygg_sats(sats: Sats, språk: str) -> list[str]:
    """Bygger upp satsens ord som lista — utan versal och punkt."""
    vf = sats.predikatfras
    delar = []

    if vf.subjektfras:
        delar.append(rendera_nominalfras(vf.subjektfras, språk))

    if vf.verb:
        delar.append(rendera_verb(vf, språk))

    # Ordföljd: svenska IO före DO, franska DO före IO
    if språk == 'sv':
        if vf.indirektobjektfras:
            delar.append(_rendera_komplement(vf.indirektobjektfras, språk))
        if vf.direktobjektfras:
            delar.append(_rendera_komplement(vf.direktobjektfras, språk))
    else:
        if vf.direktobjektfras:
            delar.append(_rendera_komplement(vf.direktobjektfras, språk))
        if vf.indirektobjektfras:
            delar.append(_rendera_komplement(vf.indirektobjektfras, språk))

    for adv in _sortera_adverbial(sats.adverbial, språk):
        delar.append(_rendera_komplement(adv, språk))

    return delar


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
    raise TypeError(f"Okänd frastyp: {type(fras)}")


def rendera_infinitivfras(inf: Infinitivfras, språk: str) -> str:
    inre_sats = inf.sats
    vf        = inre_sats.predikatfras
    lexem_id  = hämta_lexem_id(vf.verb.koncept_id, språk)
    verb_form = hämta_form(lexem_id, tempus=Tempus.INFINITIV)

    delar = [verb_form]
    for adv in _sortera_adverbial(inre_sats.adverbial, språk):
        delar.append(_rendera_komplement(adv, språk))

    verb_del = " ".join(delar)

    if språk == 'sv':
        return f"att {verb_del}"
    return verb_del  # franska: ingen infinitivpartikel (för adorer, aimer, etc.)


def rendera_bisatsfras(bf: Bisatsfras, språk: str) -> str:
    delar = []
    if bf.inledare:
        lexem_id = hämta_lexem_id(bf.inledare.koncept_id, språk)
        delar.append(hämta_form(lexem_id))
    if bf.sats:
        delar.extend(_bygg_sats(bf.sats, språk))
    return " ".join(delar)


def rendera_prepositionsfras(pf: Prepositionsfras, språk: str) -> str:
    delar = []
    if pf.preposition:
        lexem_id = hämta_lexem_id(pf.preposition.koncept_id, språk)
        delar.append(hämta_form(lexem_id))
    if pf.komplementfras:
        delar.append(_rendera_komplement(pf.komplementfras, språk))
    return " ".join(delar)


def rendera_adverbfras(af: Adverbfras, språk: str) -> str:
    lexem_id = hämta_lexem_id(af.adverb.koncept_id, språk)
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

    # Artikel
    artikel = None
    if isinstance(nf.huvuddel, Substantiv):
        if nf.species == Species.OBESTAMD:
            artikel = _artikel_obestamd(lexem_id, nf.numerus, språk)
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

    # Sätt ihop: [artikel] [adj (pre)] [substantiv] [adj (post)]
    delar = []
    if artikel:
        delar.append(artikel)
    if adj_form and adj_prenominal:
        delar.append(adj_form)
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
