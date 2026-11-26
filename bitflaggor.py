from enum import IntFlag, IntEnum


# ── Bitmasks (kan kombineras med |) ───────────────────────────────────────────

class Valens(IntFlag):
    """Verbets argumentstruktur. Styr vilka luckor som öppnas i meningsbyggaren."""
    INTRANSITIV = 1   # kan användas utan objekt
    TRANSITIV   = 2   # öppnar direktobjektlucka
    DITRANSITIV = 4   # öppnar indirektobjektlucka
    REFLEXIV    = 8   # öppnar reflexiv pronomenlucka


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
    """1 = Utrum (sv) / Maskulin (fr)   2 = Neutrum (sv) / Feminin (fr)"""
    UTRUM_MASKULIN  = 1
    NEUTRUM_FEMININ = 2


class Person(IntEnum):
    FORSTA = 1
    ANDRA  = 2
    TREDJE = 3


class Tempus(IntFlag):
    INFINITIV          =  1
    PRESENS            =  2
    PRETERITUM         =  4   # pågående/upprepad förflutenhet → sv: åt  | fr: imparfait
    SUPINUM            =  8   # används med har/hade → sv: ätit | fr: participe passé (mangé)
    IMPERATIV          = 16
    PRETERITUM_PERFEKT = 32   # avslutad förflutenhet → sv: åt (=PRETERITUM|detta) | fr: passé composé
    FUTURUM            = 64   # → sv: ingen egen form | fr: mangera


class Grad(IntEnum):
    POSITIV    = 1
    KOMPARATIV = 2
    SUPERLATIV = 3


class Semantik(IntFlag):
    """Semantiska egenskaper hos ett koncept. Används för selektionsrestriktioner."""
    ANIMAT    = 1
    KONKRET   = 2
    ABSTRAKT  = 4
    ÄTBAR     = 8
    PLATS     = 16
    MÄNSKLIG  = 32
    RÖRELSE   = 64     # verb som innebär förflyttning (springa, gå)
    RIKTNING  = 128    # preposition som kräver rörelseverb (till, från)
