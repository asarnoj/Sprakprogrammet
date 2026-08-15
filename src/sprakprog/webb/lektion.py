"""Lektionerna — en per steg på komplexitetsstegen.

TRE DELAR MED HELT OLIKA KOSTNAD, och det är hela skälet att lektionen ser ut
så här (GENERATOR.md, "Undervisning vid upplåsning"):

  PROSAN          skrivs för hand — 21 texter, inte 21 × 7. Konstruktionen är
                  språkoberoende: att en sats kan ha ett objekt är samma sak i
                  alla sju språken, och det är BARA realiseringen som skiljer.
  TABELLEN        genereras ur paradigmet, med samma axelhärledning som
                  ordboksvyn. Ingen skriver den för hand.
  EXEMPLEN        genereras av generatorn, på rätt nivå och med användarens
                  egna ord. De är därför inte samma varje gång, och det är en
                  fördel: exemplet är en färsk mening och inte en memorerad.

VAD SOM ÄR NYTT PÅ EN NIVÅ MÄTS, det härleds inte. Befolkningen körs på nivån
och på nivån under, och skillnaden är vad steget faktiskt låser upp. Det är
samma mätning som avgör vilka kort som finns, så lektionen kan inte råka
beskriva något kursen inte innehåller.

Fem av stegen införde länge NOLL nya kort, därför att samplaren aldrig byggde
dem. Det upptäcktes när den här filen skulle skrivas — en lektion om possessiver
som appen aldrig ber om vore att lära ut något oprövbart.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from ..generator import Generator
from ..generator.urval import NIVÅ

#: Prosan. En text per konstruktion, språkoberoende, i tre fält:
#: rubriken, vad konstruktionen ÄR, och vad man ska titta efter i tabellen
#: eller exemplen. `spana` är det som skiljer språken åt och därmed det som
#: är värt att läsa två gånger.
LEKTIONER: dict[int, dict[str, str]] = {
    1: {"titel": "Subject and verb",
        "vad": "The smallest complete sentence: someone, and something they do. "
               "Every other construction in this course is built on top of this "
               "one.",
        "spana": "The verb changes shape according to who the subject is. How "
                 "much it changes is the first big difference between languages "
                 "— some mark every person separately, some barely mark any."},
    2: {"titel": "Objects",
        "vad": "The thing the action happens to. 'She reads' becomes 'she reads "
               "the book'.",
        "spana": "Some languages mark the object on the noun itself, with a "
                 "case ending. Others mark it only by word order. Watch which "
                 "one you are learning — it decides how much freedom the "
                 "sentence has."},
    3: {"titel": "Definite and indefinite",
        "vad": "The difference between 'a book' and 'the book' — whether you "
               "mean any one, or a particular one both of you know about.",
        "spana": "Where the marker sits varies enormously: a separate word "
                 "before the noun, an ending glued onto it, or nothing at all. "
                 "The same distinction, three different mechanics."},
    4: {"titel": "Singular and plural",
        "vad": "One or more than one. The first place where a noun gets a "
               "second form to remember.",
        "spana": "Plural often changes more than the noun: articles, "
                 "adjectives and sometimes the verb follow along. That chain "
                 "of agreement is what makes plural feel harder than it looks."},
    5: {"titel": "Adjectives before the noun",
        "vad": "Describing the thing: 'the big house', 'a kind teacher'.",
        "spana": "An attributive adjective agrees with its noun, and in some "
                 "languages the ending depends on the article as well. That is "
                 "why the same adjective can have dozens of forms."},
    6: {"titel": "Possessives",
        "vad": "Whose it is: 'my book', 'their house'.",
        "spana": "The possessive takes the article's place — you say 'my "
                 "house', not 'the my house'. In several languages it also "
                 "agrees with the thing owned rather than the owner, which is "
                 "the opposite of what English does."},
    7: {"titel": "Indirect objects",
        "vad": "Who receives: 'she gives the book to him'.",
        "spana": "Two objects in one sentence, and the language has to keep "
                 "them apart — by case, by a preposition, or by their order. "
                 "Which of the three tells you a lot about the language."},
    8: {"titel": "Adverbs",
        "vad": "When, how, how often: 'she works today', 'he reads slowly'.",
        "spana": "Adverbs rarely inflect, so there is little to memorise — but "
                 "where they may stand in the sentence is strictly regulated, "
                 "and that is the real lesson."},
    9: {"titel": "Tense",
        "vad": "Placing the action in time: past, present, future.",
        "spana": "Some languages build tense into the verb, others use a helper "
                 "verb, and most do both depending on the tense. This is where "
                 "verbs stop having a handful of forms and start having dozens."},
    10: {"titel": "Possession with a noun",
         "vad": "'The girl's book' — the owner is a noun, not a pronoun.",
         "spana": "An ending on the owner, a preposition between them, or a "
                  "separate particle. Also watch the order: the owner comes "
                  "first in some languages and second in others."},
    11: {"titel": "Being and becoming",
         "vad": "Sentences with no action: 'she is a doctor', 'he is happy'.",
         "spana": "A predicative adjective often inflects differently from one "
                  "standing before a noun — sometimes not at all. And a "
                  "predicative noun frequently drops its article, which almost "
                  "no other position does."},
    12: {"titel": "Negation",
         "vad": "Saying that something is not the case.",
         "spana": "This unlocks no new word forms at all, yet it doubles the "
                  "number of sentences you can make. Every language does it "
                  "differently: a single word, a pair of words wrapped around "
                  "the verb, a helper verb, or an ending on the verb itself."},
    13: {"titel": "Verbs that take verbs",
         "vad": "'She wants to read', 'he begins to work'.",
         "spana": "Whether the second verb needs a marker in front of it — to, "
                  "att, zu, à, di — is a property of the FIRST verb, and it has "
                  "to be learned per verb. Where the two verbs stand relative to "
                  "each other is a property of the language."},
    14: {"titel": "The perfect",
         "vad": "'She has read the book' — done, and it still matters now.",
         "spana": "Built with a helper verb plus a special form of the main "
                  "verb. Which helper is often a property of the individual "
                  "verb, not a rule you can derive — and getting it wrong is one "
                  "of the most audible mistakes a learner makes."},
    15: {"titel": "Prepositional phrases",
         "vad": "'In the house', 'behind the tree', 'with a friend'.",
         "spana": "In some languages the preposition decides which case its "
                  "noun takes, and different prepositions demand different "
                  "cases. That government has to be learned preposition by "
                  "preposition."},
    16: {"titel": "Yes-no questions",
         "vad": "Turning a statement into a question you can answer with yes "
                "or no.",
         "spana": "No new word forms, but the biggest test of word order so "
                  "far: this is the first time the parts of the sentence swap "
                  "places instead of something being added. Six languages, six "
                  "different strategies."},
    17: {"titel": "The passive",
         "vad": "'The book is read' — the thing affected becomes the subject, "
                "and the doer can disappear.",
         "spana": "A helper verb plus a participle in most languages, but not "
                  "all — some mark it with an ending on the verb. Note that the "
                  "passive still carries tense, so it multiplies with everything "
                  "you learned in the tense lesson."},
    18: {"titel": "Comparison",
         "vad": "'Bigger', 'the biggest', 'bigger than the house'.",
         "spana": "Two more forms per adjective, and each of them still agrees "
                  "the way the plain form does — which is why comparison "
                  "multiplies an adjective's paradigm rather than adding to it."},
    19: {"titel": "Commands",
         "vad": "Telling someone to do something: 'read the book!'",
         "spana": "The subject usually disappears, but the verb still knows who "
                  "it is talking to — so there is one command form per way of "
                  "addressing someone. Languages with a polite 'you' have an "
                  "extra one."},
    20: {"titel": "Subordinate clauses",
         "vad": "A whole sentence inside another: 'she knows that he came'.",
         "spana": "Everything you can say in a main clause you can say here. "
                  "But two languages change the word order inside the "
                  "subordinate clause, and one changes the level of politeness — "
                  "so this is not simply a sentence pasted into a slot."},
    21: {"titel": "Wh-questions",
         "vad": "Asking about a part of the sentence: who, what, when, where.",
         "spana": "Most languages move the question word to the front — but not "
                  "all, and asking about the SUBJECT never inverts, because the "
                  "question word is already standing where the subject stood."},
}


class Lektioner:
    def __init__(self, språk_db: sqlite3.Connection,
                 kort_db: sqlite3.Connection) -> None:
        self.s = språk_db
        self.k = kort_db
        self._nya: dict[tuple, list] = {}

    def lista(self, språk: str, nivå: int, cefr: str) -> list[dict]:
        """De 21 stegen, med vilka som är upplåsta."""
        return [{"nivå": n, "titel": LEKTIONER[n]["titel"],
                 "nyckel": NIVÅ.get(n, "grund"), "upplåst": n <= nivå}
                for n in sorted(LEKTIONER)]

    def nya_celler(self, språk: str, nivå: int, cefr: str) -> list[dict]:
        """Kort som steget låser upp. MÄTT: befolkningen på N mot N−1.

        Samma mätning som avgör vilka kort som finns, så en lektion kan inte
        råka beskriva något kursen inte innehåller.
        """
        nyckel = (språk, nivå, cefr)
        if nyckel in self._nya:
            return self._nya[nyckel]
        import tempfile
        from pathlib import Path

        from ..kort.befolka import befolka
        from ..kort.db import anslut_kort

        def bestånd(n: int) -> dict[str, sqlite3.Row]:
            if n < 1:
                return {}
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "n.db"
                k = anslut_kort(p)
                k.executescript(
                    (Path(__file__).resolve().parents[3] / "kort.sql")
                    .read_text(encoding="utf-8"))
                befolka(k, self.s, {språk}, nivå=n, cefr=cefr)
                return {r["nyckel"]: dict(r) for r in k.execute(
                    "SELECT * FROM Kort WHERE språk = ?", (språk,))}

        nu, förr = bestånd(nivå), bestånd(nivå - 1)
        nya = [v for n, v in nu.items() if n not in förr]
        nya.sort(key=lambda r: (r["typ"], -(r["räckvidd"] or 0)))
        self._nya[nyckel] = nya
        return nya

    def exempel(self, språk: str, källspråk: str, nivå: int, cefr: str,
                antal: int = 3) -> list[dict]:
        """Färska exempelmeningar SOM ANVÄNDER konstruktionen.

        Genererade och inte skrivna, så exemplet är en ny mening varje gång
        och inte något att memorera. Kandidater som inte innehåller stegets
        konstruktion förkastas — annars visar lektionen om bisatser en mening
        utan bisats, vilket är värre än ingen mening alls.
        """
        g = Generator(self.s, self.k, språk, källspråk=källspråk,
                      nivå=nivå, cefr=cefr)
        prövare = _PRÖVARE.get(NIVÅ.get(nivå, ""))
        ut: list[dict] = []
        for _ in range(300):
            if len(ut) >= antal:
                break
            m = g.samplare.kandidat()
            if m is None or g.validator.validera(m):
                continue
            if prövare is not None and not prövare(m):
                continue
            res = g._rendera(m)
            if res is None:
                continue
            uppgift = g._rendera_källa(m) if g.källrenderare else None
            if g.källrenderare and uppgift is None:
                continue
            ut.append({"text": res[0], "uppgift": uppgift})
        return ut

    def lektion(self, språk: str, källspråk: str, nivå: int, cefr: str) -> dict:
        text = LEKTIONER[nivå]
        nya = self.nya_celler(språk, nivå, cefr)
        per_typ: dict[str, list] = {}
        for r in nya:
            per_typ.setdefault(r["typ"], []).append(r["facit"])
        return {
            "nivå": nivå, **text, "konstruktion": NIVÅ.get(nivå, "grund"),
            "exempel": self.exempel(språk, källspråk, nivå, cefr),
            "nya_kort": len(nya),
            "nytt": [{"typ": t, "antal": len(v), "prov": v[:12]}
                     for t, v in sorted(per_typ.items(), key=lambda x: -len(x[1]))],
        }


def _fras_har(m, attribut: str) -> bool:
    for fras in (m.subjekt, m.objekt, m.io):
        if fras is not None and not isinstance(fras, str) \
                and getattr(fras, attribut, None):
            return True
    return False


#: Prov på att en kandidat FAKTISKT innehåller stegets konstruktion. Utan dem
#: visar lektionen om passiv en mening i aktiv form — samplaren bygger ju bara
#: konstruktionen ibland.
_PRÖVARE = {
    "objekt": lambda m: m.objekt is not None,
    "bestämdhet": lambda m: any(
        f is not None and not isinstance(f, str)
        and getattr(f, "bestämdhet", None) is not None
        and f.bestämdhet.value == "bestämd" for f in (m.subjekt, m.objekt)),
    "numerus": lambda m: any(
        f is not None and not isinstance(f, str)
        and getattr(f, "numerus", None) is not None and f.numerus.value == "pl"
        for f in (m.subjekt, m.objekt)),
    "attribut": lambda m: _fras_har(m, "attribut"),
    "possessiv": lambda m: _fras_har(m, "possessiv"),
    "io": lambda m: m.io is not None,
    "adverbial": lambda m: any(isinstance(a, str) for a in m.adverbial),
    "tempus": lambda m: m.tid.value != "nutid",
    "genitiv": lambda m: _fras_har(m, "ägare"),
    "predikativ": lambda m: m.predikativ is not None,
    "negation": lambda m: m.negerad,
    "komplement": lambda m: m.komplement is not None,
    "perfekt": lambda m: m.aspekt.value != "perfektiv",
    "prepositionsfras": lambda m: any(
        hasattr(a, "preposition") for a in m.adverbial),
    "fråga": lambda m: m.fråga,
    "passiv": lambda m: m.diates.value != "aktiv",
    "komparation": lambda m: m.grad.value != "positiv" or any(
        getattr(a, "grad", None) is not None and a.grad.value != "positiv"
        for f in (m.subjekt, m.objekt, m.io)
        if f is not None and not isinstance(f, str)
        for a in getattr(f, "attribut", ())),
    "imperativ": lambda m: m.modus.value != "indikativ",
    "bisats": lambda m: m.bisats is not None,
    "whfråga": lambda m: m.fråga_om is not None,
}
