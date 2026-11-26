from functools import partial
from ordbokläsare import hämta_slumpmässigt_koncept_id

class Ordklass:
    def __init__(self, ordklasser: list, förälder: object, förälderattribut: str):
        self.ordklasser = ordklasser
        self.substantiv = None
        self.verb = None
        self.adjektiv = None
        self.adverb = None
        self.pronomen = None
        self.preposition = None
        self.konjunktion = None
        self.subjunktion = None
        self.determinantiv = None
        self.frågepronomen = None
        self.frågadverb = None
        self.interrogativdeterminant = None
        self.negationsadverb = None
        self.förälder = förälder
        self.förälderattribut = förälderattribut

    def skapa_ordklass(self, ordklass: str):
        if not getattr(self, ordklass):
            klass = ordklass.capitalize()
            koncept_id = hämta_slumpmässigt_koncept_id(klass)
            ordklassinstans = globals()[klass](koncept_id)
            setattr(self.förälder, self.förälderattribut, ordklassinstans)
        return self.förälder

    def generera_dict(self):
        ordklass_dict = {}
        for ordklass in self.ordklasser:
            ordklass_dict[ordklass] = (None, partial(self.skapa_ordklass, ordklass))
        return ordklass_dict


class Substantiv:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Verb:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

    def __str__(self):
        return f"Verb({self.koncept_id})"

class Adjektiv:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Adverb:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Pronomen:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Preposition:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Konjunktion:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Subjunktion:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Determinantiv:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Frågepronomen:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Frågadverb:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Interrogativdeterminant:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id

class Negationsadverb:
    def __init__(self, koncept_id: int):
        self.koncept_id = koncept_id
