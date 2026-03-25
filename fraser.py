from ordklasser import *
from ordbokläsare import *
from böjningar import *
from bitflaggor import Valens
from functools import partial

def hämta(self, namn: str):
    return getattr(self, namn)

def skapa(self, namn: str):
    klass = namn.capitalize()
    setattr(self, namn, globals()[klass](self))
    return self

class Sats:
    def __init__(self, förälder=None):
        self.predikatfras = None
        self.adverbial    = []   # lista: Adverbfras, Prepositionsfras, Nominalfras, Bisatsfras, ...
        self.förälder     = förälder

    def skapa_predikatfras(self):
        if not self.predikatfras:
            self.predikatfras = Verbfras(self)
        return self

    def skapa_adverbial(self, frastyp='adverbfras'):
        """Lägg till ett adverbial i listan. frastyp styr vilken fras som skapas."""
        klasser = {
            'adverbfras':       Adverbfras,
            'prepositionsfras': Prepositionsfras,
            'bisatsfras':       Bisatsfras,
            'nominalfras':      Nominalfras,
        }
        ny = klasser.get(frastyp, Adverbfras)(self)
        self.adverbial.append(ny)
        return ny

    def generera_dict(self):
        sats_dict = {}

        if self.predikatfras:
            sats_dict['predikatfras'] = (self.predikatfras, partial(hämta, self, 'predikatfras'))
        else:
            sats_dict['predikatfras'] = (None, self.skapa_predikatfras)

        if self.predikatfras:
            for i, adv in enumerate(self.adverbial):
                sats_dict[f'adverbial[{i}]'] = (adv, partial(hämta, self, 'adverbial'))
            sats_dict['+ adverbial'] = (None, self.skapa_adverbial)

        return sats_dict
    
    def __str__(self):
        return "Sats"

class Fras:
    def __init__(self, fraser: list, förälder: object, förälderattribut: str = None):
        self.fraser = fraser
        self.nominalfras = None
        self.adjektivfras = None
        self.adverbfras = None
        self.verbfras = None
        self.prepositionsfras = None
        self.infinitivfras = None
        self.bisatsfras = None
        self.förälder = förälder
        self.förälderattribut = förälderattribut

    def skapa_fras(self, fras: str):
        if not getattr(self, fras):
            # Capitalize first letter to match class name (e.g., "nominalfras" -> "Nominalfras")
            klass = fras.capitalize()
            
            # Create the new fras instance (e.g., Nominalfras)
            frasinstans = globals()[klass](self.förälder)
            
            # Set the new fras instance to the parent's attribute
            # e.g., if förälderattribut is "subjektfras", this sets self.förälder.subjektfras = frasinstans
            setattr(self.förälder, self.förälderattribut, frasinstans)

        return self.förälder
    
    def generera_dict(self):
        fras_dict = {}
        for fras in self.fraser:
            fras_dict[fras] = (None, partial(self.skapa_fras, fras))
        return fras_dict

class Nominalfras:
    def __init__ (self, förälder=None):
        self.huvuddel = None
        self.determinant = None
        self.attribut = None
        self.frasattribut = None

        self.numerus = None
        self.species = None
        self.kasus = None

        self.förälder = förälder

    def skapa_huvuddel(self):
        self.huvuddel = Ordklass(["substantiv", "pronomen"], self, "huvuddel")
        return self.huvuddel

    def skapa_determinant(self):
        self.determinant = Determinantiv(input("Ange determinant: "))
        return self

    def skapa_attribut(self):
        self.attribut = Adjektivfras(self)
        return self

    def skapa_frasattribut(self):
        self.frasattribut = Fras(["prepositionsfras", "bisatsfras"], self, "frasattribut")
        return self.frasattribut

    def generera_dict(self):
        subjekt_dict = {}

        if self.huvuddel:
            subjekt_dict['huvuddel'] = (self.huvuddel, partial(hämta, self, 'huvuddel'))
        else:
            subjekt_dict['huvuddel'] = (None, self.skapa_huvuddel)

        if self.huvuddel:
            if self.determinant:
                subjekt_dict['determinant'] = (self.determinant, partial(hämta, self, 'determinant'))
            else:
                subjekt_dict['determinant'] = (None, self.skapa_determinant)

        if self.huvuddel:
            if self.attribut:
                subjekt_dict['attribut'] = (self.attribut, partial(hämta, self, 'attribut'))
            else:
                subjekt_dict['attribut'] = (None, self.skapa_attribut)

        if self.huvuddel:
            if self.frasattribut:
                subjekt_dict['frasattribut'] = (self.frasattribut, partial(hämta, self, 'frasattribut'))
            else:
                subjekt_dict['frasattribut'] = (None, self.skapa_frasattribut)

        return subjekt_dict
    
    def __str__(self):
        nominalfras = []
        if self.determinant:
            nominalfras.append(f"determinant: {self.determinant}")
        if self.attribut:
            nominalfras.append(f"attribut: {self.attribut}")
        if self.huvuddel:
            nominalfras.append(f"huvuddel: {self.huvuddel}")
        if self.frasattribut:
            nominalfras.append(f"frasattribut: {self.frasattribut}")
        if nominalfras == []:
            return "<Nominalfras>"
        else:
            return " ".join(nominalfras)
        
class Adjektivfras:
    def __init__(self, förälder=None):
        self.adjektiv = None
        self.attribut = None
        self.grad     = None  # Positiv / Komparativ / Superlativ
        self.förälder = förälder

    def skapa_adjektiv(self):
        self.adjektiv = Adjektiv(input("Ange adjektiv: "))
        return self

    def skapa_attribut(self):
        self.attribut = Adverb(input("Ange attribut: "))
        return self

    def generera_dict(self):
        adjektivfras_dict = {}

        if self.adjektiv:
            adjektivfras_dict['adjektiv'] = (self.adjektiv, partial(hämta, self, 'adjektiv'))
        else:
            adjektivfras_dict['adjektiv'] = (None, self.skapa_adjektiv)

        if self.attribut:
            adjektivfras_dict['attribut'] = (self.attribut, partial(hämta, self, 'attribut'))
        else:
            adjektivfras_dict['attribut'] = (None, self.skapa_attribut)

        return adjektivfras_dict
    
    def __str__(self):
        return "<Adjektivfras>"
    
class Adverbfras:
    def __init__(self, förälder=None):
        self.adverb = None
        self.attribut = None
        self.förälder = förälder

    def skapa_adverb(self):
        self.adverb = Adverb(input("Ange adverb: "))
        return self

    def skapa_attribut(self):
        self.attribut = Adverb(input("Ange attribut: "))
        return self

    def generera_dict(self):
        adverbfras_dict = {}

        if self.adverb:
            adverbfras_dict['adverb'] = (self.adverb, partial(hämta, self, 'adverb'))
        else:
            adverbfras_dict['adverb'] = (None, self.skapa_adverb)

        if self.attribut:
            adverbfras_dict['attribut'] = (self.attribut, partial(hämta, self, 'attribut'))
        else:
            adverbfras_dict['attribut'] = (None, self.skapa_attribut)

        return adverbfras_dict
    
    def __str__(self):
        return "<Adverbfras>"
    
class Verbfras:
    def __init__(self, förälder):
        self.verb = None
        self.subjektfras = None
        self.direktobjektfras = None
        self.indirektobjektfras = None

        self.tempus  = None
        self.person  = None  # 1/2/3 – relevant för fr, None för sv
        self.numerus = None  # 1=Singular, 2=Plural – relevant för fr, None för sv

        self.förälder = förälder

    def skapa_verb(self):
        self.verb = Verb(hämta_slumpmässigt_koncept_id("Verb"))
        return self

    def skapa_subjektfras(self):
        self.subjektfras = Fras(["nominalfras", "prepositionsfras", "infinitivfras", "bisatsfras"], self, "subjektfras")
        return self.subjektfras
    
    def skapa_direktobjektfras(self):
        self.direktobjektfras = Fras(["nominalfras", "prepositionsfras", "infinitivfras", "bisatsfras"], self, "direktobjektfras")
        return self.direktobjektfras
    
    def skapa_indirektobjektfras(self):
        self.indirektobjektfras = Fras(["nominalfras", "prepositionsfras", "infinitivfras", "bisatsfras"], self, "indirektobjektfras")
        return self.indirektobjektfras
    

    def skapa_tempus(self):
        self.tempus = Tempus(self, "tempus")
        return self.tempus


    def generera_dict(self):
        verbfras_dict = {}

        if self.verb:
            verbfras_dict['verb'] = (self.verb, self.skapa_verb)
        else:
            verbfras_dict['verb'] = (None, self.skapa_verb)

        if self.verb:
            if self.subjektfras:
                verbfras_dict['subjektfras'] = (self.subjektfras, partial(hämta, self, 'subjektfras'))
            else:
                verbfras_dict['subjektfras'] = (None, self.skapa_subjektfras)

        if self.verb:
            valens = Valens(kolla_lexems_egenskap(hämta_lexem_id(self.verb.koncept_id, 'sv'), "valens") or 0)

            if Valens.TRANSITIV in valens or Valens.DITRANSITIV in valens:
                if self.direktobjektfras:
                    verbfras_dict['direktobjektfras'] = (self.direktobjektfras, partial(hämta, self, 'direktobjektfras'))
                else:
                    verbfras_dict['direktobjektfras'] = (None, self.skapa_direktobjektfras)

            if Valens.DITRANSITIV in valens:
                if self.indirektobjektfras:
                    verbfras_dict['indirektobjektfras'] = (self.indirektobjektfras, partial(hämta, self, 'indirektobjektfras'))
                else:
                    verbfras_dict['indirektobjektfras'] = (None, self.skapa_indirektobjektfras)

        if self.verb:
            if self.tempus:
                verbfras_dict['tempus'] = (self.tempus, self.skapa_tempus)
            else:
                verbfras_dict['tempus'] = (None, self.skapa_tempus)

        return verbfras_dict
    
    def __str__(self):
        return f"<Verbfras verb={self.verb}>"

class Prepositionsfras:
    def __init__(self, förälder=None):
        self.preposition = None
        self.komplementfras = None
        self.förälder = förälder

    def skapa_preposition(self):
        self.preposition = Preposition(input("Ange preposition: "))
        return self

    def skapa_komplementfras(self):
        self.komplementfras = Fras(["nominalfras", "infinitivfras", "bisatsfras"], self, "komplementfras")
        return self.komplementfras

    def generera_dict(self):
        prepositionsfras_dict = {}

        if self.preposition:
            prepositionsfras_dict['preposition'] = (self.preposition, partial(hämta, self, 'preposition'))
        else:
            prepositionsfras_dict['preposition'] = (None, self.skapa_preposition)

        if self.komplementfras:
            prepositionsfras_dict['komplementfras'] = (self.komplementfras, partial(hämta, self, 'komplementfras'))
        else:
            prepositionsfras_dict['komplementfras'] = (None, self.skapa_komplementfras)

        return prepositionsfras_dict
    
    def __str__(self):
        return "<Prepositionsfras>"
    
class Infinitivfras:
    def __init__(self, förälder=None):
        self.sats     = None   # inre Sats — predikatfras + adverbial
        self.förälder = förälder

    def skapa_sats(self):
        if not self.sats:
            self.sats = Sats(self)
        return self.sats

    def generera_dict(self):
        inf_dict = {}
        if self.sats:
            inf_dict['sats'] = (self.sats, partial(hämta, self, 'sats'))
        else:
            inf_dict['sats'] = (None, self.skapa_sats)
        return inf_dict

    def __str__(self):
        return "<Infinitivfras>"

class Bisatsfras:
    def __init__(self, förälder=None):
        self.inledare = None
        self.sats = None
        self.förälder = förälder

    def skapa_inledare(self):
        self.inledare = Ordklass(["subjunktion", "konjunktion"], self, "inledare")
        return self.inledare

    def skapa_bisats(self):
        self.sats = Sats(self)
        return self.sats

    def generera_dict(self):
        bisatsfras_dict = {}

        if self.inledare:
            bisatsfras_dict['inledare'] = (self.inledare, partial(hämta, self, 'inledare'))
        else:
            bisatsfras_dict['inledare'] = (None, self.skapa_inledare)

        if self.sats:
            bisatsfras_dict['sats'] = (self.sats, partial(hämta, self, 'sats'))
        else:
            bisatsfras_dict['sats'] = (None, self.skapa_bisats)

        return bisatsfras_dict


class Samordningsled:
    """Ett konjunktion–sats-par som binder en sats till föregående.
    Invariant: konjunktion och sats är alltid obligatoriska tillsammans.
    sats är låst tills konjunktion är satt.
    """
    def __init__(self, förälder=None):
        self.konjunktion = None
        self.sats        = None
        self.förälder    = förälder

    def är_komplett(self) -> bool:
        return self.konjunktion is not None and self.sats is not None

    def skapa_konjunktion(self):
        self.konjunktion = Konjunktion(hämta_slumpmässigt_koncept_id("Konjunktion"))
        return self

    def skapa_sats(self):
        self.sats = Sats(self)
        return self.sats

    def generera_dict(self):
        led_dict = {}

        if self.konjunktion:
            led_dict['konjunktion'] = (self.konjunktion, partial(hämta, self, 'konjunktion'))
        else:
            led_dict['konjunktion'] = (None, self.skapa_konjunktion)

        # sats är låst tills konjunktion är satt
        if self.konjunktion:
            if self.sats:
                led_dict['sats'] = (self.sats, partial(hämta, self, 'sats'))
            else:
                led_dict['sats'] = (None, self.skapa_sats)

        return led_dict

    def __str__(self):
        return "<Samordningsled>"


class Mening:
    """Den fullständiga meningen: en huvud-Sats plus noll eller flera Samordningsled.
    Invariant: ett nytt Samordningsled kan bara läggas till när huvud är satt
    och det senaste ledet är komplett (konjunktion + sats båda fyllda).
    """
    def __init__(self):
        self.huvud        = None
        self.samordningar = []   # list[Samordningsled]

    def skapa_huvud(self):
        if not self.huvud:
            self.huvud = Sats(self)
        return self.huvud

    def skapa_samordningsled(self):
        led = Samordningsled(self)
        self.samordningar.append(led)
        return led

    def generera_dict(self):
        mening_dict = {}

        if self.huvud:
            mening_dict['huvud'] = (self.huvud, partial(hämta, self, 'huvud'))
        else:
            mening_dict['huvud'] = (None, self.skapa_huvud)

        if self.huvud:
            for i, led in enumerate(self.samordningar):
                mening_dict[f'samordningsled[{i}]'] = (led, partial(lambda i, s: s.samordningar[i], i, self))
            # Nytt led låst om senaste ännu inte är komplett
            if not self.samordningar or self.samordningar[-1].är_komplett():
                mening_dict['+ samordningsled'] = (None, self.skapa_samordningsled)

        return mening_dict

    def __str__(self):
        return "<Mening>"