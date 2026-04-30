from enum import IntFlag, IntEnum


# ── Bitmasks (kan kombineras med |) ───────────────────────────────────────────

class Valens(IntFlag):
    """Verbets argumentstruktur. Styr vilka luckor som öppnas i meningsbyggaren."""
    INTRANSITIV = 1   # kan användas utan objekt
    TRANSITIV   = 2   # öppnar direktobjektlucka
    DITRANSITIV = 4   # öppnar indirektobjektlucka
    REFLEXIV    = 8   # öppnar reflexiv pronomenlucka
    KOPULA      = 16  # öppnar predikativlucka (vara, bli, verka …)


class Frastyp(IntFlag):
    """Vilken syntaktisk frastyp som krävs i en slot. Bitmask i MönsterKrav.frastyp."""
    NOMINALFRAS      = 1
    ADJEKTIVFRAS     = 2
    PREPOSITIONSFRAS = 4
    ADVERBFRAS       = 8
    INFINITIVFRAS    = 16
    BISATSFRAS       = 32


class Personlighet(IntFlag):
    """Om verbet tar ett riktigt subjekt eller ett opersonligt 'det'/'il'."""
    PERSONLIG  = 1
    OPERSONLIG = 2


class Kasus(IntFlag):
    """Nominalfrasens syntaktiska roll. En form kan täcka flera kasus (bitmask)."""
    NOMINATIV = 1
    ACKUSATIV = 2
    DATIV     = 4
    GENITIV   = 8


# ── Exklusiva värden (IntEnum, bara ett värde i taget) ────────────────────────

class Numerus(IntEnum):
    SINGULAR = 1
    PLURAL   = 2


class Species(IntEnum):
    OBESTAMD = 1
    BESTAMD  = 2


class Genus(IntEnum):
    """
    sv: 1=Utrum          2=Neutrum
    fr/es/it: 1=Maskulin 2=Feminin
    de: 1=Maskulin       2=Feminin   3=Neutrum
    """
    UTRUM_MASKULIN  = 1
    NEUTRUM_FEMININ = 2
    DE_NEUTRUM      = 3   # bara tyska


class Person(IntEnum):
    FORSTA = 1
    ANDRA  = 2
    TREDJE = 3


class Tempus(IntFlag):
    INFINITIV          =   1
    PRESENS            =   2
    PRETERITUM         =   4   # pågående/upprepad förflutenhet → sv: åt  | fr: imparfait
    SUPINUM            =   8   # används med har/hade → sv: ätit | fr: participe passé (mangé)
    IMPERATIV          =  16
    PRETERITUM_PERFEKT =  32   # avslutad förflutenhet → sv: åt (=PRETERITUM|detta) | fr: passé composé
    FUTURUM            =  64   # → sv: ingen egen form | fr: mangera
    TE_FORM            = 128   # ja: て-form / gerundium
    NEGATIV            = 256   # ja: ない-form (verb) / くない-form (i-adjektiv)
    POTENTIAL          = 512   # ja: 可能形


class Grad(IntEnum):
    POSITIV    = 1
    KOMPARATIV = 2
    SUPERLATIV = 3


class Semantik(IntFlag):
    """Bakåtkompatibel alias — används av test_semantik.py. Ny kod bör använda ordklassspecifika klasser."""
    ANIMAT    = 1
    KONKRET   = 2
    ABSTRAKT  = 4
    ÄTBAR     = 8
    PLATS     = 16
    MÄNSKLIG  = 32
    RÖRELSE   = 64
    RIKTNING  = 128


class SubstantivSemantics(IntFlag):
    """Semantiska egenskaper för substantiv. Bitar tolkas bara för Koncept med ordklass='Substantiv'."""
    ANIMAT   = 1    # levande varelse som rör sig på egen hand (djur, människa)
    KONKRET  = 2    # har fysisk existens (bord, äpple, bil)
    ABSTRAKT = 4    # idé, känsla eller egenskap utan fysisk form (frihet, glädje)
    ÄTBAR    = 8    # kan ätas eller drickas (äpple, bröd, vin)
    PLATS    = 16   # geografisk plats eller lokation (stad, strand, rum)
    MÄNSKLIG = 32   # en människa eller mänsklig roll (lärare, soldat, barn)
    RÖRELSE  = 64   # sak som typiskt rör sig eller transporterar (bil, flod, vind)
    RIKTNING = 128  # riktning eller orienterat läge (norr, höger, uppfart)
    HÄNDELSE = 256  # händelse som kan anordnas eller deltas i (fest, möte, match)
    TID      = 512  # tidsperiod eller tidpunkt (dag, år, morgon, decennium, april)


class VerbSemantics(IntFlag):
    """Semantiska egenskaper för verb. Bitar tolkas bara för Koncept med ordklass='Verb'."""
    RÖRELSE       = 1   # innebär förflyttning i rummet (gå, springa, flyga)
    RIKTNING      = 2   # kräver vanligen riktning som komplement (svänga, rikta, peka)
    KOMMUNIKATION = 4   # förmedla information (säga, fråga, berätta, skriva)
    PERCEPTION    = 8   # sensorisk upplevelse (se, höra, känna, lukta)
    KOGNITION     = 16  # tanke eller vetande (tänka, tro, veta, förstå)


class AdverbSemantics(IntFlag):
    """Semantiska egenskaper för adverb. Bitar tolkas bara för Koncept med ordklass='Adverb'."""
    RÖRELSE  = 1    # beskriver förflyttning (fort, sakta i rörelsekontext)
    RIKTNING = 2    # anger riktning (framåt, bakåt, uppåt, hit, dit)
    TID      = 4    # anger tidpunkt eller tidsrelation (nu, igår, snart, redan)
    FREKVENS = 8    # anger hur ofta (ofta, sällan, aldrig, alltid)
    GRAD     = 16   # anger intensitet (mycket, ganska, lite, extremt, nästan)
    SÄTT     = 32   # anger hur något görs, sättsadverb (försiktigt, gärna, tyst)
