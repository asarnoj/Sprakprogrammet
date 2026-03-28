from fraser import (Sats, Verbfras, Nominalfras, Adjektivfras, Infinitivfras,
                    Adverbfras, Bisatsfras, Prepositionsfras, Mening, Samordningsled,
                    Frågepronomensfras, Frågadverbfras, Negationsadverbfras)
from ordklasser import (Verb, Substantiv, Pronomen, Adjektiv, Adverb, Subjunktion,
                        Preposition, Konjunktion, Frågepronomen, Frågadverb,
                        Interrogativdeterminant, Negationsadverb)
from bitflaggor import Kasus, Numerus, Species, Tempus, Grad

def han_äter_en_boll() -> Sats:
    """He eats a ball."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb    = Verb(koncept_id=1)  # eat
    vf.tempus  = Tempus.PRESENS


    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.OBESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats

def han_äter_en_röd_boll() -> Sats:
    """He eats a red ball."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb    = Verb(koncept_id=1)  # eat
    vf.tempus  = Tempus.PRESENS


    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.OBESTAMD
    objekt.kasus    = Kasus.ACKUSATIV

    af = Adjektivfras(objekt)
    af.adjektiv = Adjektiv(koncept_id=7)  # red
    af.grad     = Grad.POSITIV
    objekt.attribut = af

    vf.direktobjektfras = objekt

    return sats

def han_åt_en_röd_boll() -> Sats:
    """He ate a red ball."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb    = Verb(koncept_id=1)  # eat
    vf.tempus  = Tempus.PRETERITUM


    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.OBESTAMD
    objekt.kasus    = Kasus.ACKUSATIV

    af = Adjektivfras(objekt)
    af.adjektiv = Adjektiv(koncept_id=7)  # red
    af.grad     = Grad.POSITIV
    objekt.attribut = af

    vf.direktobjektfras = objekt

    return sats


def lärarna_har_gett_barnen_böckerna() -> Sats:
    """The kind teacher has given the tired children the most beautiful books."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb    = Verb(koncept_id=10)  # give
    vf.tempus  = Tempus.PRETERITUM_PERFEKT


    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Substantiv(koncept_id=9)   # teacher
    subjekt.numerus  = Numerus.SINGULAR
    subjekt.species  = Species.BESTAMD
    subjekt.kasus    = Kasus.NOMINATIV
    af_subj = Adjektivfras(subjekt)
    af_subj.adjektiv = Adjektiv(koncept_id=8)     # kind
    af_subj.grad     = Grad.POSITIV
    subjekt.attribut = af_subj
    vf.subjektfras   = subjekt

    indir = Nominalfras(vf)
    indir.huvuddel = Substantiv(koncept_id=12)    # child
    indir.numerus  = Numerus.PLURAL
    indir.species  = Species.BESTAMD
    indir.kasus    = Kasus.DATIV
    af_indir = Adjektivfras(indir)
    af_indir.adjektiv = Adjektiv(koncept_id=11)   # tired
    af_indir.grad     = Grad.POSITIV
    indir.attribut    = af_indir
    vf.indirektobjektfras = indir

    direkt = Nominalfras(vf)
    direkt.huvuddel = Substantiv(koncept_id=13)   # book
    direkt.numerus  = Numerus.PLURAL
    direkt.species  = Species.BESTAMD
    direkt.kasus    = Kasus.ACKUSATIV
    af_direkt = Adjektivfras(direkt)
    af_direkt.adjektiv = Adjektiv(koncept_id=14)  # beautiful
    af_direkt.grad     = Grad.SUPERLATIV
    direkt.attribut    = af_direkt
    vf.direktobjektfras = direkt

    return sats


def trötta_läraren_springer_i_parken() -> Sats:
    """The tired teacher runs in the beautiful park."""
    sats = Sats()
    vf = Verbfras(sats)
    sats.predikatfras = vf
    vf.verb   = Verb(koncept_id=17)   # run
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Substantiv(koncept_id=9)    # teacher
    subjekt.numerus  = Numerus.SINGULAR
    subjekt.species  = Species.BESTAMD
    subjekt.kasus    = Kasus.NOMINATIV
    af_subj = Adjektivfras(subjekt)
    af_subj.adjektiv = Adjektiv(koncept_id=11)     # tired
    af_subj.grad     = Grad.POSITIV
    subjekt.attribut = af_subj
    vf.subjektfras   = subjekt

    pp = Prepositionsfras(vf)
    pp.preposition = Preposition(koncept_id=21)    # in

    park_nf = Nominalfras(pp)
    park_nf.huvuddel = Substantiv(koncept_id=22)   # park
    park_nf.numerus  = Numerus.SINGULAR
    park_nf.species  = Species.BESTAMD
    park_nf.kasus    = Kasus.ACKUSATIV
    af_park = Adjektivfras(park_nf)
    af_park.adjektiv = Adjektiv(koncept_id=14)     # beautiful
    af_park.grad     = Grad.POSITIV
    park_nf.attribut = af_park
    pp.komplementfras = park_nf

    sats.adverbial = [pp]
    return sats


def jag_tror_att_läraren_har_gett_böckerna() -> Sats:
    """I believe that the kind teacher has given the tired children the most beautiful books."""
    sats = Sats()

    # Huvudsats: "Jag tror att ..."
    vf = Verbfras(sats)
    sats.predikatfras = vf
    vf.verb   = Verb(koncept_id=19)   # believe
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=15)   # I
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras   = subjekt

    # Bisatsfras: "att den snälla läraren har gett de trötta barnen de vackraste böckerna"
    bf = Bisatsfras(vf)
    bf.inledare = Subjunktion(koncept_id=20)     # that / att / que

    inre_sats = Sats(bf)
    inre_vf   = Verbfras(inre_sats)
    inre_sats.predikatfras = inre_vf
    inre_vf.verb   = Verb(koncept_id=10)         # give
    inre_vf.tempus = Tempus.PRETERITUM_PERFEKT

    inre_subj = Nominalfras(inre_vf)
    inre_subj.huvuddel = Substantiv(koncept_id=9)    # teacher
    inre_subj.numerus  = Numerus.SINGULAR
    inre_subj.species  = Species.BESTAMD
    inre_subj.kasus    = Kasus.NOMINATIV
    af_subj = Adjektivfras(inre_subj)
    af_subj.adjektiv   = Adjektiv(koncept_id=8)      # kind
    af_subj.grad       = Grad.POSITIV
    inre_subj.attribut = af_subj
    inre_vf.subjektfras = inre_subj

    indir = Nominalfras(inre_vf)
    indir.huvuddel = Substantiv(koncept_id=12)        # child
    indir.numerus  = Numerus.PLURAL
    indir.species  = Species.BESTAMD
    indir.kasus    = Kasus.DATIV
    af_indir = Adjektivfras(indir)
    af_indir.adjektiv = Adjektiv(koncept_id=11)       # tired
    af_indir.grad     = Grad.POSITIV
    indir.attribut    = af_indir
    inre_vf.indirektobjektfras = indir

    direkt = Nominalfras(inre_vf)
    direkt.huvuddel = Substantiv(koncept_id=13)       # book
    direkt.numerus  = Numerus.PLURAL
    direkt.species  = Species.BESTAMD
    direkt.kasus    = Kasus.ACKUSATIV
    af_direkt = Adjektivfras(direkt)
    af_direkt.adjektiv = Adjektiv(koncept_id=14)      # beautiful
    af_direkt.grad     = Grad.SUPERLATIV
    direkt.attribut    = af_direkt
    inre_vf.direktobjektfras = direkt

    bf.sats            = inre_sats
    vf.direktobjektfras = bf

    return sats


def jag_älskar_att_springa_snabbt() -> Sats:
    """I love to run fast."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=16)   # love
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=15)  # I
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras   = subjekt

    inf      = Infinitivfras(vf)
    inf_sats = Sats(inf)
    inf.sats = inf_sats

    inf_vf        = Verbfras(inf_sats)
    inf_vf.verb   = Verb(koncept_id=17)   # run
    inf_vf.tempus = Tempus.INFINITIV
    inf_sats.predikatfras = inf_vf

    af            = Adverbfras(inf_sats)
    af.adverb     = Adverb(koncept_id=18)   # quickly
    inf_sats.adverbial = [af]

    vf.direktobjektfras = inf

    return sats


def han_äter_en_boll_och_springer_i_parken() -> Mening:
    """He eats a ball and he runs in the park."""
    mening = Mening()

    # Huvud: "Han äter en boll"
    sats1 = Sats(mening)
    mening.huvud = sats1

    vf1 = Verbfras(sats1)
    sats1.predikatfras = vf1
    vf1.verb   = Verb(koncept_id=1)    # eat
    vf1.tempus = Tempus.PRESENS

    subj1 = Nominalfras(vf1)
    subj1.huvuddel = Pronomen(koncept_id=4)   # he
    subj1.kasus    = Kasus.NOMINATIV
    vf1.subjektfras = subj1

    obj1 = Nominalfras(vf1)
    obj1.huvuddel = Substantiv(koncept_id=2)  # ball
    obj1.numerus  = Numerus.SINGULAR
    obj1.species  = Species.OBESTAMD
    obj1.kasus    = Kasus.ACKUSATIV
    vf1.direktobjektfras = obj1

    # Samordningsled: "och han springer i parken"
    led = Samordningsled(mening)
    led.konjunktion = Konjunktion(koncept_id=23)   # and

    sats2 = Sats(led)
    led.sats = sats2

    vf2 = Verbfras(sats2)
    sats2.predikatfras = vf2
    vf2.verb   = Verb(koncept_id=17)   # run
    vf2.tempus = Tempus.PRESENS

    subj2 = Nominalfras(vf2)
    subj2.huvuddel = Pronomen(koncept_id=4)   # he
    subj2.kasus    = Kasus.NOMINATIV
    vf2.subjektfras = subj2

    pp = Prepositionsfras(sats2)
    pp.preposition = Preposition(koncept_id=21)    # in
    park_nf = Nominalfras(pp)
    park_nf.huvuddel = Substantiv(koncept_id=22)   # park
    park_nf.numerus  = Numerus.SINGULAR
    park_nf.species  = Species.BESTAMD
    pp.komplementfras = park_nf
    sats2.adverbial = [pp]

    mening.samordningar = [led]
    return mening


def läraren_springer_men_tror_att_han_ger_böckerna() -> Mening:
    """The tired teacher runs quickly in the beautiful park, but I believe that he gives the kind children the most beautiful books often at school."""

    mening = Mening()

    # ── Sats 1: "Den trötta läraren springer snabbt i den vackra parken" ──────
    sats1 = Sats(mening)
    mening.huvud = sats1

    vf1 = Verbfras(sats1)
    sats1.predikatfras = vf1
    vf1.verb   = Verb(koncept_id=17)   # run
    vf1.tempus = Tempus.PRESENS

    subj1 = Nominalfras(vf1)
    subj1.huvuddel = Substantiv(koncept_id=9)   # teacher
    subj1.numerus  = Numerus.SINGULAR
    subj1.species  = Species.BESTAMD
    subj1.kasus    = Kasus.NOMINATIV
    af1 = Adjektivfras(subj1)
    af1.adjektiv   = Adjektiv(koncept_id=11)     # tired
    af1.grad       = Grad.POSITIV
    subj1.attribut = af1
    vf1.subjektfras = subj1

    # Adverbial 1: snabbt
    adv1 = Adverbfras(sats1)
    adv1.adverb = Adverb(koncept_id=18)          # quickly
    sats1.adverbial.append(adv1)

    # Adverbial 2: i den vackra parken
    pp1 = Prepositionsfras(sats1)
    pp1.preposition = Preposition(koncept_id=21)  # in
    park_nf = Nominalfras(pp1)
    park_nf.huvuddel = Substantiv(koncept_id=22)  # park
    park_nf.numerus  = Numerus.SINGULAR
    park_nf.species  = Species.BESTAMD
    park_nf.kasus    = Kasus.ACKUSATIV
    af_park = Adjektivfras(park_nf)
    af_park.adjektiv = Adjektiv(koncept_id=14)    # beautiful
    af_park.grad     = Grad.POSITIV
    park_nf.attribut  = af_park
    pp1.komplementfras = park_nf
    sats1.adverbial.append(pp1)

    # ── Samordningsled: "men jag tror att..." ─────────────────────────────────
    led = Samordningsled(mening)
    led.konjunktion = Konjunktion(koncept_id=24)  # but

    sats2 = Sats(led)
    led.sats = sats2

    vf2 = Verbfras(sats2)
    sats2.predikatfras = vf2
    vf2.verb   = Verb(koncept_id=19)   # believe
    vf2.tempus = Tempus.PRESENS

    subj2 = Nominalfras(vf2)
    subj2.huvuddel = Pronomen(koncept_id=15)     # I
    subj2.kasus    = Kasus.NOMINATIV
    vf2.subjektfras = subj2

    # Bisatsfras: "att han ger de snälla barnen de vackraste böckerna ofta i skolan"
    bf = Bisatsfras(vf2)
    bf.inledare = Subjunktion(koncept_id=20)     # that

    inre = Sats(bf)
    inre_vf = Verbfras(inre)
    inre.predikatfras = inre_vf
    inre_vf.verb   = Verb(koncept_id=10)         # give
    inre_vf.tempus = Tempus.PRESENS

    inre_subj = Nominalfras(inre_vf)
    inre_subj.huvuddel = Pronomen(koncept_id=4)  # he
    inre_subj.kasus    = Kasus.NOMINATIV
    inre_vf.subjektfras = inre_subj

    indir = Nominalfras(inre_vf)
    indir.huvuddel = Substantiv(koncept_id=12)   # child
    indir.numerus  = Numerus.PLURAL
    indir.species  = Species.BESTAMD
    indir.kasus    = Kasus.DATIV
    af_indir = Adjektivfras(indir)
    af_indir.adjektiv = Adjektiv(koncept_id=8)   # kind
    af_indir.grad     = Grad.POSITIV
    indir.attribut    = af_indir
    inre_vf.indirektobjektfras = indir

    direkt = Nominalfras(inre_vf)
    direkt.huvuddel = Substantiv(koncept_id=13)  # book
    direkt.numerus  = Numerus.PLURAL
    direkt.species  = Species.BESTAMD
    direkt.kasus    = Kasus.ACKUSATIV
    af_direkt = Adjektivfras(direkt)
    af_direkt.adjektiv = Adjektiv(koncept_id=14) # beautiful
    af_direkt.grad     = Grad.SUPERLATIV
    direkt.attribut    = af_direkt
    inre_vf.direktobjektfras = direkt

    # Adverbial 3: ofta
    adv3 = Adverbfras(inre)
    adv3.adverb = Adverb(koncept_id=26)          # often
    inre.adverbial.append(adv3)

    # Adverbial 4: i skolan
    pp2 = Prepositionsfras(inre)
    pp2.preposition = Preposition(koncept_id=21)  # in
    skola_nf = Nominalfras(pp2)
    skola_nf.huvuddel = Substantiv(koncept_id=27) # school
    skola_nf.numerus  = Numerus.SINGULAR
    skola_nf.species  = Species.BESTAMD
    skola_nf.kasus    = Kasus.ACKUSATIV
    pp2.komplementfras = skola_nf
    inre.adverbial.append(pp2)

    bf.sats = inre
    vf2.direktobjektfras = bf

    mening.samordningar = [led]
    return mening


def han_äter_bollen() -> Sats:
    """He eats the ball."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb    = Verb(koncept_id=1)   # eat
    vf.tempus  = Tempus.PRESENS


    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.BESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


# ── FRÅGOR ────────────────────────────────────────────────────────────────

def vem_äter_bollen() -> Sats:
    """Who eats the ball?  (frågepronomen som subjekt — normal V2-ordföljd)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Frågepronomensfras(vf)
    subjekt.frågepronomen = Frågepronomen(koncept_id=29)  # who
    subjekt.kasus         = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.BESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def vad_äter_han() -> Sats:
    """What does he eat?  (frågepronomen som objekt — frontering + V-S-inversion)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Frågepronomensfras(vf)
    objekt.frågepronomen = Frågepronomen(koncept_id=30)  # what
    objekt.kasus         = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def var_springer_han() -> Sats:
    """Where does he run?  (frågadverb — frontering + V-S-inversion)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=17)  # run
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    fråga_adv = Frågadverbfras(sats)
    fråga_adv.frågadverb = Frågadverb(koncept_id=31)  # where
    sats.adverbial = [fråga_adv]

    return sats


def äter_han_bollen() -> Sats:
    """Does he eat the ball?  (ja/nej-fråga — V-S-inversion utan frågeord)"""
    sats = Sats()
    sats.ja_nej_fråga = True

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.BESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def vem_äter_vad() -> Sats:
    """Who eats what?  (flera frågeord — naturlig ordföljd)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Frågepronomensfras(vf)
    subjekt.frågepronomen = Frågepronomen(koncept_id=29)  # who
    subjekt.kasus         = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Frågepronomensfras(vf)
    objekt.frågepronomen = Frågepronomen(koncept_id=30)  # what
    objekt.kasus         = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def vilken_bok_äter_han() -> Sats:
    """Which book does he eat?  (interrogativ determinant — frontering + V-S-inversion)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel    = Substantiv(koncept_id=13)  # book
    objekt.determinant = Interrogativdeterminant(koncept_id=35)  # which
    objekt.numerus     = Numerus.SINGULAR
    objekt.species     = Species.OBESTAMD
    objekt.kasus       = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


# ── KOMPLEXA FRÅGOR ──────────────────────────────────────────────────────

def vem_gav_vilken_bok_till_barnen() -> Sats:
    """Who gave which beautiful book to the tired children?
    (frågepronomen som subjekt + interrogativ determinant som DO
     + PP-adverbial "till barnen" — flera frågeord → naturlig ordföljd)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=10)   # give
    vf.tempus = Tempus.PRETERITUM

    # Subjekt: vem (frågepronomen)
    subjekt = Frågepronomensfras(vf)
    subjekt.frågepronomen = Frågepronomen(koncept_id=29)  # who
    subjekt.kasus         = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    # Direkt objekt: vilken vacker bok (interrogativ determinant + adjektiv)
    direkt = Nominalfras(vf)
    direkt.huvuddel    = Substantiv(koncept_id=13)  # book
    direkt.determinant = Interrogativdeterminant(koncept_id=35)  # which
    direkt.numerus     = Numerus.SINGULAR
    direkt.species     = Species.OBESTAMD
    direkt.kasus       = Kasus.ACKUSATIV
    af_direkt = Adjektivfras(direkt)
    af_direkt.adjektiv = Adjektiv(koncept_id=14)  # beautiful
    af_direkt.grad     = Grad.POSITIV
    direkt.attribut    = af_direkt
    vf.direktobjektfras = direkt

    # Adverbial: till de trötta barnen (prepositionsfras)
    pp = Prepositionsfras(sats)
    pp.preposition = Preposition(koncept_id=28)  # to/till/à

    barn_nf = Nominalfras(pp)
    barn_nf.huvuddel = Substantiv(koncept_id=12)   # child
    barn_nf.numerus  = Numerus.PLURAL
    barn_nf.species  = Species.BESTAMD
    barn_nf.kasus    = Kasus.ACKUSATIV  # PP-komplement, inte IO — prepositionen hanterar dativbetydelsen
    af_barn = Adjektivfras(barn_nf)
    af_barn.adjektiv = Adjektiv(koncept_id=11)     # tired
    af_barn.grad     = Grad.POSITIV
    barn_nf.attribut = af_barn
    pp.komplementfras = barn_nf

    sats.adverbial = [pp]

    return sats


def vad_tror_han_att_läraren_ger_barnen() -> Mening:
    """What does he believe that the kind teacher gives the children?
    (frågepronomen som DO i huvudsats + bisats med vanligt innehåll
     — enda frågeordet → frontering + inversion)"""
    mening = Mening()

    sats = Sats(mening)
    mening.huvud = sats

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=19)  # believe
    vf.tempus = Tempus.PRESENS

    # Subjekt: han
    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    # Direkt objekt: bisatsfras "att den snälla läraren ger barnen [vad]"
    # Men frågeordet "vad" hör semantiskt till bisatsens verb "ger",
    # men syntaktiskt fronteras det ur huvudsatsen.
    # I vårt system: "vad" ersätter DO i huvudsatsen (hela bisatsen ersätts av vad).
    # Meningen blir: "Vad tror han?"  med bisatsen som separat sats.
    # Alternativt: vi bygger hela bisatskonstruktionen.
    # Låt oss bygga: "Vad tror han att den snälla läraren ger de trötta barnen?"
    # → vad som DO i huvudsatsen fungerar inte riktigt med bisatsen...
    #
    # Enklare tolkning: huvudsats har "vad" som DO (ersätter bisatsfrasen)
    # → "Vad tror han?" — men det testar inte bisatsen.
    #
    # Bättre: bygg en Mening med ja/nej-fråga + bisats
    # "Tror han att den snälla läraren har gett de trötta barnen böckerna?"

    sats.ja_nej_fråga = True

    # Direkt objekt: bisatsfras
    bf = Bisatsfras(vf)
    bf.inledare = Subjunktion(koncept_id=20)  # that/att

    inre = Sats(bf)
    inre_vf = Verbfras(inre)
    inre.predikatfras = inre_vf
    inre_vf.verb   = Verb(koncept_id=10)  # give
    inre_vf.tempus = Tempus.PRETERITUM_PERFEKT

    # Inre subjekt: den snälla läraren
    inre_subj = Nominalfras(inre_vf)
    inre_subj.huvuddel = Substantiv(koncept_id=9)   # teacher
    inre_subj.numerus  = Numerus.SINGULAR
    inre_subj.species  = Species.BESTAMD
    inre_subj.kasus    = Kasus.NOMINATIV
    af_subj = Adjektivfras(inre_subj)
    af_subj.adjektiv = Adjektiv(koncept_id=8)       # kind
    af_subj.grad     = Grad.POSITIV
    inre_subj.attribut = af_subj
    inre_vf.subjektfras = inre_subj

    # Inre IO: de trötta barnen
    indir = Nominalfras(inre_vf)
    indir.huvuddel = Substantiv(koncept_id=12)       # child
    indir.numerus  = Numerus.PLURAL
    indir.species  = Species.BESTAMD
    indir.kasus    = Kasus.DATIV
    af_indir = Adjektivfras(indir)
    af_indir.adjektiv = Adjektiv(koncept_id=11)      # tired
    af_indir.grad     = Grad.POSITIV
    indir.attribut    = af_indir
    inre_vf.indirektobjektfras = indir

    # Inre DO: de vackraste böckerna
    direkt = Nominalfras(inre_vf)
    direkt.huvuddel = Substantiv(koncept_id=13)      # book
    direkt.numerus  = Numerus.PLURAL
    direkt.species  = Species.BESTAMD
    direkt.kasus    = Kasus.ACKUSATIV
    af_direkt = Adjektivfras(direkt)
    af_direkt.adjektiv = Adjektiv(koncept_id=14)     # beautiful
    af_direkt.grad     = Grad.SUPERLATIV
    direkt.attribut    = af_direkt
    inre_vf.direktobjektfras = direkt

    bf.sats = inre
    vf.direktobjektfras = bf

    return mening


def vem_springer_var_och_äter_han_bollen() -> Mening:
    """Who runs where, and does he eat the ball?
    (samordnad mening: sats 1 med två frågeord + sats 2 som ja/nej-fråga
     — testar frågor i samordnade satser + skiljetecken från sista satsen)"""
    mening = Mening()

    # ── Sats 1: "Vem springer var?" (flera frågeord → naturlig ordföljd) ──
    sats1 = Sats(mening)
    mening.huvud = sats1

    vf1 = Verbfras(sats1)
    sats1.predikatfras = vf1

    vf1.verb   = Verb(koncept_id=17)  # run
    vf1.tempus = Tempus.PRESENS

    subj1 = Frågepronomensfras(vf1)
    subj1.frågepronomen = Frågepronomen(koncept_id=29)  # who
    subj1.kasus         = Kasus.NOMINATIV
    vf1.subjektfras = subj1

    adv1 = Frågadverbfras(sats1)
    adv1.frågadverb = Frågadverb(koncept_id=31)  # where
    sats1.adverbial = [adv1]

    # ── Samordningsled: "och äter han bollen?" (ja/nej) ───────────────────
    led = Samordningsled(mening)
    led.konjunktion = Konjunktion(koncept_id=23)  # and

    sats2 = Sats(led)
    sats2.ja_nej_fråga = True
    led.sats = sats2

    vf2 = Verbfras(sats2)
    sats2.predikatfras = vf2

    vf2.verb   = Verb(koncept_id=1)   # eat
    vf2.tempus = Tempus.PRESENS

    subj2 = Nominalfras(vf2)
    subj2.huvuddel = Pronomen(koncept_id=4)  # he
    subj2.kasus    = Kasus.NOMINATIV
    vf2.subjektfras = subj2

    obj2 = Nominalfras(vf2)
    obj2.huvuddel = Substantiv(koncept_id=2)  # ball
    obj2.numerus  = Numerus.SINGULAR
    obj2.species  = Species.BESTAMD
    obj2.kasus    = Kasus.ACKUSATIV
    vf2.direktobjektfras = obj2

    mening.samordningar = [led]
    return mening


# ── NEGATIONER ─────────────────────────────────────────────────────────────

def han_äter_inte_bollen() -> Sats:
    """He does not eat the ball."""
    sats = Sats()
    sats.negation = True

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.BESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def han_har_inte_ätit_bollen() -> Sats:
    """He has not eaten the ball."""
    sats = Sats()
    sats.negation = True

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRETERITUM_PERFEKT

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.BESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def äter_han_inte_bollen() -> Sats:
    """Does he not eat the ball?"""
    sats = Sats()
    sats.ja_nej_fråga = True
    sats.negation     = True

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.BESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def har_han_inte_ätit_bollen() -> Sats:
    """Has he not eaten the ball?"""
    sats = Sats()
    sats.ja_nej_fråga = True
    sats.negation     = True

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRETERITUM_PERFEKT

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Nominalfras(vf)
    objekt.huvuddel = Substantiv(koncept_id=2)  # ball
    objekt.numerus  = Numerus.SINGULAR
    objekt.species  = Species.BESTAMD
    objekt.kasus    = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def vad_äter_han_inte() -> Sats:
    """What does he not eat?  (frontat frågeord + negation)"""
    sats = Sats()
    sats.negation = True

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=1)   # eat
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    objekt = Frågepronomensfras(vf)
    objekt.frågepronomen = Frågepronomen(koncept_id=30)  # what
    objekt.kasus         = Kasus.ACKUSATIV
    vf.direktobjektfras = objekt

    return sats


def jag_tror_att_han_inte_äter_bollen() -> Sats:
    """I believe that he does not eat the ball.  (negation i bisats — BIFF-regeln)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=19)  # believe
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=15)  # I
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    # Bisatsfras: "att han inte äter bollen"
    bf = Bisatsfras(vf)
    bf.inledare = Subjunktion(koncept_id=20)  # that

    inre = Sats(bf)
    inre.negation = True   # ← negation i bisatsen

    inre_vf = Verbfras(inre)
    inre.predikatfras = inre_vf
    inre_vf.verb   = Verb(koncept_id=1)   # eat
    inre_vf.tempus = Tempus.PRESENS

    inre_subj = Nominalfras(inre_vf)
    inre_subj.huvuddel = Pronomen(koncept_id=4)  # he
    inre_subj.kasus    = Kasus.NOMINATIV
    inre_vf.subjektfras = inre_subj

    inre_obj = Nominalfras(inre_vf)
    inre_obj.huvuddel = Substantiv(koncept_id=2)  # ball
    inre_obj.numerus  = Numerus.SINGULAR
    inre_obj.species  = Species.BESTAMD
    inre_obj.kasus    = Kasus.ACKUSATIV
    inre_vf.direktobjektfras = inre_obj

    bf.sats = inre
    vf.direktobjektfras = bf

    return sats


def han_älskar_att_inte_springa() -> Sats:
    """He loves to not run.  (negation i infinitivfras)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf

    vf.verb   = Verb(koncept_id=16)   # love
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    inf      = Infinitivfras(vf)
    inf_sats = Sats(inf)
    inf_sats.negation = True   # ← negation i infinitivfrasen
    inf.sats = inf_sats

    inf_vf        = Verbfras(inf_sats)
    inf_vf.verb   = Verb(koncept_id=17)   # run
    inf_vf.tempus = Tempus.INFINITIV
    inf_sats.predikatfras = inf_vf

    vf.direktobjektfras = inf

    return sats


# ── NEGATIONSADVERB ────────────────────────────────────────────────────────

def han_springer_aldrig() -> Sats:
    """He never runs."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf
    vf.verb   = Verb(koncept_id=17)   # run
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    naf = Negationsadverbfras(sats)
    naf.negationsadverb = Negationsadverb(koncept_id=36)  # never
    sats.adverbial = [naf]

    return sats


def springer_han_aldrig() -> Sats:
    """Does he never run?  (negationsadverb + ja/nej-inversion)"""
    sats = Sats()
    sats.ja_nej_fråga = True

    vf = Verbfras(sats)
    sats.predikatfras = vf
    vf.verb   = Verb(koncept_id=17)   # run
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    naf = Negationsadverbfras(sats)
    naf.negationsadverb = Negationsadverb(koncept_id=36)  # never
    sats.adverbial = [naf]

    return sats


def han_springer_inte_längre() -> Sats:
    """He no longer runs."""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf
    vf.verb   = Verb(koncept_id=17)   # run
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    naf = Negationsadverbfras(sats)
    naf.negationsadverb = Negationsadverb(koncept_id=37)  # no longer
    sats.adverbial = [naf]

    return sats


def läraren_tror_aldrig_att_han_äter() -> Sats:
    """The teacher never believes that he eats.  (negationsadverb i bisats — BIFF-regeln)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf
    vf.verb   = Verb(koncept_id=19)   # believe
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Substantiv(koncept_id=9)  # teacher
    subjekt.numerus  = Numerus.SINGULAR
    subjekt.species  = Species.BESTAMD
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    # Negationsadverb i huvudsatsen
    naf = Negationsadverbfras(sats)
    naf.negationsadverb = Negationsadverb(koncept_id=36)  # never
    sats.adverbial.append(naf)

    # Bisatsfras som objekt
    bf = Bisatsfras(vf)
    bf.inledare = Subjunktion(koncept_id=20)  # that

    inre = Sats(bf)
    inre_vf = Verbfras(inre)
    inre.predikatfras = inre_vf
    inre_vf.verb   = Verb(koncept_id=1)   # eat
    inre_vf.tempus = Tempus.PRESENS

    inre_subj = Nominalfras(inre_vf)
    inre_subj.huvuddel = Pronomen(koncept_id=4)  # he
    inre_subj.kasus    = Kasus.NOMINATIV
    inre_vf.subjektfras = inre_subj

    bf.sats = inre
    vf.direktobjektfras = bf

    return sats


def han_älskar_att_aldrig_springa() -> Sats:
    """He loves to never run.  (negationsadverb i infinitivfras)"""
    sats = Sats()

    vf = Verbfras(sats)
    sats.predikatfras = vf
    vf.verb   = Verb(koncept_id=16)   # love
    vf.tempus = Tempus.PRESENS

    subjekt = Nominalfras(vf)
    subjekt.huvuddel = Pronomen(koncept_id=4)  # he
    subjekt.kasus    = Kasus.NOMINATIV
    vf.subjektfras = subjekt

    inf      = Infinitivfras(vf)
    inf_sats = Sats(inf)
    inf.sats = inf_sats

    inf_vf        = Verbfras(inf_sats)
    inf_vf.verb   = Verb(koncept_id=17)   # run
    inf_vf.tempus = Tempus.INFINITIV
    inf_sats.predikatfras = inf_vf

    naf = Negationsadverbfras(inf_sats)
    naf.negationsadverb = Negationsadverb(koncept_id=36)  # never
    inf_sats.adverbial = [naf]

    vf.direktobjektfras = inf

    return sats
