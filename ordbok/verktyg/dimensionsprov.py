"""Projektionen av den universella cellistan — håller den?

Fyra invarianter, och den tredje är den som bär hela idén: varje ändelse i
varje tabell ska läras ut EXAKT en gång. Lärs den ut två gånger är stegen
full av tomma moment; lärs den aldrig ut går den inte att lära sig.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

# MODULEN, inte namnen. `from … import projicera` binder funktionen vid
# import, och då når falsifieringens patch den aldrig — alla fyra proven höll
# med sabotaget påslaget första gången de kördes. Ett prov som inte kan
# fällas bevisar ingenting, och det gällde här hela filen.
import sprakprog.kort.dimensioner as d                       # noqa: E402

projicera = lambda *a, **kw: d.projicera(*a, **kw)            # noqa: E731
universella_celler = lambda *a, **kw: d.universella_celler(*a, **kw)  # noqa: E731
ändelsetabeller = lambda *a, **kw: d.ändelsetabeller(*a, **kw)        # noqa: E731


def prov_delmängd() -> list[str]:
    """Varje stege är en DELFÖLJD av den universella listan, i samma ordning.

    Det är vad "en universell lista, projicerad" betyder. Kan ett språk
    kasta om ordningen är listan inte längre delad utan sju listor.
    """
    fel, u = [], list(universella_celler())
    for språk, steg in projicera().items():
        index = [u.index(c) for c, _ in steg if c in u]
        if len(index) != len(steg):
            fel.append(f"{språk}: steg utanför den universella listan")
        elif index != sorted(index):
            fel.append(f"{språk}: stegen är omkastade mot listan")
    return fel


def prov_ingen_upprepning() -> list[str]:
    """Ingen klass lär ut samma ändelse två gånger. Det är hela urvalet."""
    fel = []
    tabeller = ändelsetabeller()
    for språk, steg in projicera().items():
        sedd: dict[str, set[str]] = {}
        for cell, klasser in steg:
            for klass in klasser:
                # `.get`, inte indexering: sabotaget släpper igenom celler
                # som klassen inte HAR, och en krasch är ett sämre besked än
                # ett fall — provet ska säga vad som är fel, inte dö av det.
                ändelse = tabeller[(språk, klass)].get(cell)
                if ändelse is None:
                    fel.append(f"{språk}/{klass}: {cell} finns inte i tabellen")
                    continue
                if ändelse in sedd.setdefault(klass, set()):
                    fel.append(f"{språk}/{klass}: {ändelse!r} lärs ut igen "
                               f"på {cell}")
                sedd[klass].add(ändelse)
    return fel


def prov_allt_lärs_ut() -> list[str]:
    """Varje ändelse som finns i en tabell ska läras ut någon gång.

    Motsatsen till provet ovan, och den farligare: en ändelse som ingen cell
    introducerar är omöjlig att lära sig, och det syns inte förrän någon
    skriver fel på den.
    """
    fel = []
    tabeller = ändelsetabeller()
    projektion = projicera()
    for (språk, klass), tabell in tabeller.items():
        lärda = {tabell[cell] for cell, klasser in projektion.get(språk, [])
                 if klass in klasser and cell in tabell}
        for saknad in set(tabell.values()) - lärda:
            fel.append(f"{språk}/{klass}: ändelsen {saknad!r} lärs aldrig ut")
    return fel


def prov_stegen_viks() -> list[str]:
    """Stegen ska bli OLIKA lång i olika språk — annars gör projektionen inget.

    Det här är provet mot att kriteriet tyst slutar diskriminera. Skulle
    `projicera` börja släppa igenom varje cell för varje språk blir alla
    stegar lika långa som listan, och ingenting hade sagt ifrån.
    """
    p = projicera()
    längder = {s: len(steg) for s, steg in p.items()}
    if len(set(längder.values())) < 2:
        return [f"alla språk fick lika många steg ({längder}) — projektionen "
                f"skiljer inte längre på språken"]
    if max(längder.values()) >= len(universella_celler()):
        return [f"ett språk fick hela listan ({max(längder.values())} steg) — "
                f"kriteriet filtrerar inte"]
    return []


SPRÅK = ("sv", "en", "de", "fr", "es", "it", "ja")


def prov_stegen_är_hel() -> list[str]:
    """Den flätade stegen innehåller ALLT, en gång var.

    Tappar flätningen en konstruktion går den aldrig att låsa upp; tappar den
    en böjningscell är ändelsen otillgänglig igen — samma fel som hela
    projektionen finns för att laga, återinfört ett steg senare.
    """
    from sprakprog.generator.urval import NIVÅ
    fel = []
    for språk in SPRÅK:
        s = d.stege(språk)
        # NAMNET ÄR EN TUPEL sedan grundböjningen blev ett steg som bär hela
        # presensparadigmet. Att läsa det som en sträng gav en lista av
        # tuplar och ett prov som föll på fel grund.
        k = [n for t, namn in s if t == "konstruktion" for n in namn]
        b = [n for t, namn in s if t == "böjning" for n in namn]
        väntad_b = [c for c, _ in d.projicera().get(språk, [])]
        if sorted(k) != sorted(NIVÅ.values()):
            fel.append(f"{språk}: konstruktionerna stämmer inte ({len(k)} av "
                       f"{len(NIVÅ)})")
        if sorted(b) != sorted(väntad_b):
            fel.append(f"{språk}: böjningsstegen stämmer inte ({len(b)} av "
                       f"{len(väntad_b)})")
        if len(set(k)) != len(k) or len(set(b)) != len(b):
            fel.append(f"{språk}: något steg förekommer två gånger")
    return fel


def prov_beroenden() -> list[str]:
    """En konstruktion får aldrig komma före den böjning den kräver.

    Utan det lägger den proportionella flätningen "tempus" på steg 9 medan
    preteritumändelserna kommer på steg 30 — och användaren möter dåtid
    trettio steg innan något kort lär ut hur den böjs.

    PROVET HAR SIN EGEN KOPIA AV KRAVEN, och det är inte dubbelarbete. Först
    läste det `d.BEROENDE`, alltså exakt det sabotaget tömmer — och då hade
    provet inget att kontrollera och gick igenom. Ett prov som läser sin egen
    förutsättning ur det som prövas kan aldrig falla.

    Kraven här är den grammatiska sanningen: dåtid kräver dåtidsformer,
    perfekt kräver participet, imperativ kräver imperativformer, passiv
    kräver passiva former. Skulle modulens tabell säga något annat är det
    HÄR som säger ifrån.
    """
    KRAV = {"tempus": ("Pret", "Imperf", "Fut"),
            "perfekt": ("Sup", "PresPer"),
            "imperativ": ("Imp",),
            "passiv": None}          # None = diates Passiv, inte en tempus
    from sprakprog.kaikki_mappning.paradigm import ladda_legend, ladda_slot
    legend = ladda_legend()
    tempusnamn = {v: k for k, v in legend.get("tempus", {}).items()}
    fel = []
    for språk in SPRÅK:
        s = d.stege(språk)
        plats = {n: i for i, (_, namn) in enumerate(s) for n in namn}
        try:
            axlar = {c.id: c.axlar
                     for c in ladda_slot(språk, "Verb", legend).celler}
        except FileNotFoundError:
            continue
        for konstruktion, tempus in KRAV.items():
            if konstruktion not in plats:
                continue
            celler = [n for t, namn in s if t == "böjning" for n in namn if (
                (axlar.get(n, {}).get("diates") == 2) if tempus is None
                else tempusnamn.get(axlar.get(n, {}).get("tempus")) in tempus)]
            if celler and plats[celler[-1]] > plats[konstruktion]:
                fel.append(f"{språk}: {konstruktion} på steg "
                           f"{plats[konstruktion] + 1} men {celler[-1]} först "
                           f"på {plats[celler[-1]] + 1}")
    return fel


def prov_varvas() -> list[str]:
    """De två sorterna ska VARVAS, inte ligga i två block.

    Ligger all böjning först och alla konstruktioner sedan är det två stegar
    efter varandra och inte en flätad, och då har flätningen slutat göra
    något utan att säga ifrån.
    """
    fel = []
    for språk in SPRÅK:
        typer = [t for t, _ in d.stege(språk)]
        if len(set(typer)) < 2:
            continue                       # bara en sort finns att varva
        byten = sum(a != b for a, b in zip(typer, typer[1:]))
        if byten < 4:
            fel.append(f"{språk}: bara {byten} byten mellan sorterna — "
                       f"stegen är block, inte flätad")
    return fel


def _befolkad():
    """En färsk kortdatabas med hela beståndet. Byggs en gång och delas."""
    global _CACHE
    if _CACHE is None:
        import tempfile
        from sprakprog.db import anslut
        from sprakprog.kort.befolka import befolka
        from sprakprog.kort.db import skapa_kortdatabas
        katalog = tempfile.mkdtemp()
        db = skapa_kortdatabas(Path(katalog) / "prov.db")
        befolka(db, anslut(), set(SPRÅK), cefr="C2", mät=False)
        _CACHE = db
    return _CACHE


_CACHE = None


def prov_inget_tomt_läromoment() -> list[str]:
    """Två ändelsekort i samma klass får aldrig ha samma svar.

    Franskans K0 hade `pres_1sg = e` och `pres_3sg = e` som TVÅ kort. Det
    andra kunde inte lära ut något — har man klarat det första finns
    ingenting kvar att kunna. Mätt över alla sju språken var **52 % av
    ändelsekorten** sådana: 831 kort för 394 kunskaper, och tyskan ensam 241
    för 39.

    Kortet hör därför till ÄNDELSEN och inte till cellen. Invarianten är att
    hopslagningen faktiskt sker: samma svar i samma klass betyder samma kort.
    """
    db = _befolkad()
    fel = []
    for r in db.execute(
            """SELECT språk, ordklass, klass, facit, COUNT(*) n
               FROM Kort WHERE typ = 'system'
               GROUP BY språk, ordklass, klass, facit HAVING n > 1"""):
        fel.append(f"{r['språk']}/{r['klass']}: {r['facit']!r} finns som "
                   f"{r['n']} kort — {r['n'] - 1} av dem lär inte ut något")
    return fel


def prov_varje_cell_har_ett_kort() -> list[str]:
    """Varje cell med en ändelse ska peka på ett kort.

    DET FARLIGA MED HOPSLAGNINGEN, och skälet att den valdes framför att
    grinda bort celler: en cell utan kort går inte att attribuera. Meningen
    `Elle parle.` slår upp `pres_3sg`, och finns inget kort där kan ändelsen
    varken prövas eller skyllas på. Hopslagningen ska ta bort det tomma
    momentet UTAN att lämna hålet.
    """
    import csv as _csv
    from sprakprog.kort.dimensioner import ÄNDELSEFIL
    db = _befolkad()
    kort = {(r["språk"], r["ordklass"], r["klass"], r["facit"])
            for r in db.execute(
                "SELECT språk, ordklass, klass, facit FROM Kort WHERE typ='system'")}
    fel = []
    with ÄNDELSEFIL.open(encoding="utf-8") as f:
        for rad in _csv.DictReader(f, delimiter="\t"):
            nyckel = (rad["språk"], rad["ordklass"], rad["klass"],
                      rad["ändelse"] or "∅")
            if nyckel not in kort:
                fel.append(f"{rad['språk']}/{rad['klass']}/{rad['cell']}: "
                           f"ändelsen {rad['ändelse'] or '∅'!r} har inget kort")
    return fel[:6]


def prov_migrationen_bevarar_historiken() -> list[str]:
    """Ett cell-nycklat ändelsekort ska föras över, inte lämnas kvar.

    KORTETS IDENTITET ÄNDRADES, och det är den farligaste sortens ändring:
    de gamla korten blir inte fel, de blir OSYNLIGA. Utan migrationen står de
    kvar med sin historik men utan rad i `Cellkort` — schemalagda, förfallna,
    och omöjliga för någon mening att nå. Mätt på Julius franska: 15
    föräldralösa kort efter en nivåupplåsning, varav 7 med historik. Det är
    exakt A3:s spökkort, självförvållade.

    Provet bygger ett gammalt kort med historik, kör `befolka`, och kräver
    tre saker: kortet är borta, repetitionsraden finns kvar, och den pekar på
    efterföljaren.
    """
    import tempfile
    from sprakprog.db import anslut
    from sprakprog.kort.befolka import befolka
    from sprakprog.kort.db import skapa_kortdatabas
    db = skapa_kortdatabas(Path(tempfile.mkdtemp()) / "mig.db")
    # Ett kort med den GAMLA nyckeln: franskans K0, cellen pres_3sg, `e`.
    db.execute(
        """INSERT INTO Kort (nyckel, typ, språk, ordklass, klass, cell, facit,
                             räckvidd, stabilitet, svårighet, tillstånd, steg,
                             sedd, förfaller, antal, fall)
           VALUES ('system:fr:::Verb:K0:pres_3sg::', 'system', 'fr', 'Verb',
                   'K0', 'pres_3sg', 'e', 122, 3.5, 5.0, 2, NULL,
                   '2026-08-01T09:00:00+00:00', '2026-08-20T09:00:00+00:00',
                   4, 1)""")
    gammalt = db.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    db.execute("""INSERT INTO Repetition (kort_id, tidpunkt, betyg)
                  VALUES (?, '2026-08-01T09:00:00+00:00', 3)""", (gammalt,))
    db.commit()
    befolka(db, anslut(), {"fr"}, cefr="C2", mät=False)

    fel = []
    if db.execute("SELECT 1 FROM Kort WHERE id = ?", (gammalt,)).fetchone():
        fel.append("det cell-nycklade kortet står kvar")
    rad = db.execute(
        "SELECT kort_id FROM Repetition WHERE tidpunkt = '2026-08-01T09:00:00+00:00'"
    ).fetchone()
    if rad is None:
        fel.append("repetitionsraden försvann med kortet")
    else:
        ny = db.execute("SELECT typ, facit, cell FROM Kort WHERE id = ?",
                        (rad["kort_id"],)).fetchone()
        if ny is None:
            fel.append("repetitionsraden pekar på ett kort som inte finns")
        elif not (ny["typ"] == "system" and ny["facit"] == "e"
                  and ny["cell"] is None):
            fel.append(f"historiken hamnade på fel kort: {dict(ny)}")
    db.close()
    return fel


def prov_nivå_ett_går_att_tala_på() -> list[str]:
    """Varje verbcell en NIVÅ 1-mening slår upp ska ha ett kort.

    DET HÄR ÄR PROVET SOM AVGÖR OM GRINDEN GÅR ATT SLÅ PÅ. Utan det bygger
    generatorn meningar vars ändelser inget kort täcker, och då är
    kunskapen både oprövbar och oattribuerbar — precis felet böjningsstegen
    fanns för att laga, återinfört av sin egen grind.

    Mätt under bygget, med en cell per steg: franskans nivå 1 byggde 165
    meningar varav tio slog upp `pres_2pl` som låg på nivå 5, och engelskan
    hade samma hål på `inf_imp` i 13 av 164. Grundböjningen är därför ETT
    steg — hela presensparadigmet öppnas på en gång, eftersom delarna inte
    går att låsa upp var för sig utan att generatorn måste veta vilka subjekt
    som är tillåtna.

    PROVET RENDERAR, det resonerar inte. Samma väg som `nåbara` tar.
    """
    import random
    import tempfile
    from sprakprog.db import anslut
    from sprakprog.generator.urval import Ordförråd, Samplare
    from sprakprog.kort.befolka import befolka
    from sprakprog.kort.db import skapa_kortdatabas
    from sprakprog.rendering import RENDERARE, RenderingsFel, Uppslag, Validator

    sp = anslut()
    katalog = Path(tempfile.mkdtemp())
    fel = []
    for språk in SPRÅK:
        db = skapa_kortdatabas(katalog / f"{språk}.db")
        _, celler = d.upplåst_vid(språk, 1)
        befolka(db, sp, {språk}, cefr="A1", mät=False,
                böjningsceller={(språk, "Verb"): celler})
        täckta = {r["cell"] for r in db.execute(
            """SELECT DISTINCT c.cell FROM Cellkort c JOIN Kort k ON k.id = c.kort_id
               WHERE c.språk = ? AND k.typ = 'system' AND k.ordklass = 'Verb'""",
            (språk,))}
        renderare = RENDERARE[språk](sp)
        validator = Validator(sp)
        samplare = Samplare(Ordförråd(sp, språk, "A1"), 1, random.Random(0))
        rörda: list = []
        original = Uppslag.form
        Uppslag.form = lambda själv, lex, cell: (
            rörda.append((lex["id"], cell)) or original(själv, lex, cell))
        hål: set[str] = set()
        try:
            for _ in range(60):
                m = samplare.kandidat()
                if m is None or validator.validera(m):
                    continue
                rörda.clear()
                try:
                    renderare.rendera(m)
                except (RenderingsFel, KeyError, ValueError):
                    continue
                for lid, cell in rörda:
                    if cell in täckta:
                        continue
                    rad = sp.execute(
                        """SELECT k.ordklass FROM Lexem l
                           JOIN Koncept k ON k.id = l.koncept_id WHERE l.id = ?""",
                        (lid,)).fetchone()
                    if rad and rad["ordklass"] == "Verb":
                        hål.add(cell)
        finally:
            Uppslag.form = original
        db.close()
        if hål:
            fel.append(f"{språk}: nivå 1 bygger meningar som slår upp "
                       f"{', '.join(sorted(hål))} — celler utan kort")
    sp.close()
    return fel


PROV = [("stegen är en delföljd av listan", prov_delmängd),
        ("ingen ändelse lärs ut två gånger", prov_ingen_upprepning),
        ("varje ändelse lärs ut någon gång", prov_allt_lärs_ut),
        ("stegen viks olika per språk", prov_stegen_viks),
        ("den flätade stegen är hel", prov_stegen_är_hel),
        ("konstruktion aldrig före sin böjning", prov_beroenden),
        ("de två sorterna varvas", prov_varvas),
        ("inget tomt läromoment", prov_inget_tomt_läromoment),
        ("varje cell har ett kort", prov_varje_cell_har_ett_kort),
        ("migrationen bevarar historiken", prov_migrationen_bevarar_historiken),
        ("nivå 1 går att tala på", prov_nivå_ett_går_att_tala_på)]



# VARJE INVARIANT BEHÖVER SITT EGET SABOTAGE, och det lärde det här provet
# mig på det hårda sättet. Ett enda sabotage — "släpp igenom varje cell" —
# fällde bara två av fyra, och de andra två såg då stumma ut fast de var
# riktiga. De vaktar mot ANDRA fel: omkastning och för lite undervisning, och
# ett sabotage som lär ut för mycket kan inte bryta någon av dem.
#
# Ett prov som inte faller för sitt eget sabotage är stumt. Ett prov som inte
# faller för NÅGON ANNANS är bara ett annat prov.

def _sabotage_omkastad():
    """Stegen byggs i omvänd ordning mot listan."""
    äkta = d.projicera
    def bakvänt(celler=None, ordklass="Verb"):
        return {s: list(reversed(v)) for s, v in äkta(celler, ordklass).items()}
    d.projicera = bakvänt
    return lambda: setattr(d, "projicera", äkta)


def _sabotage_halva():
    """Varannan cell tappas — ändelser som ingen cell längre lär ut."""
    äkta = d.projicera
    def halvt(celler=None, ordklass="Verb"):
        return {s: v[::2] for s, v in äkta(celler, ordklass).items()}
    d.projicera = halvt
    return lambda: setattr(d, "projicera", äkta)


def _sabotage_utan_filter():
    """Före projektionen: varje cell blev ett steg i varje språk."""
    import sprakprog.kort.dimensioner as d
    äkta = d.projicera
    def allt(celler=None, ordklass="Verb"):
        celler = celler or d.universella_celler(ordklass)
        t = d.ändelsetabeller(ordklass)
        ut = {}
        for språk in sorted({s for s, _ in t}):
            klasser = {k for s, k in t if s == språk}
            ut[språk] = [(c, klasser) for c in celler]
        return ut
    d.projicera = allt
    return lambda: setattr(d, "projicera", äkta)

def _sabotage_utan_beroenden():
    """Beroendetabellen tömd — ren proportionell flätning."""
    äkta = d.BEROENDE, d.PASSIVKONSTRUKTION
    d.BEROENDE, d.PASSIVKONSTRUKTION = {}, "\0"
    def ångra():
        d.BEROENDE, d.PASSIVKONSTRUKTION = äkta
    return ångra


def _sabotage_två_block():
    """All böjning först, alla konstruktioner sedan — två stegar, inte en."""
    äkta = d.stege
    def block(språk, ordklass="Verb"):
        s = äkta(språk, ordklass)
        return ([x for x in s if x[0] == "böjning"]
                + [x for x in s if x[0] == "konstruktion"])
    d.stege = block
    return lambda: setattr(d, "stege", äkta)


def _sabotage_tappa_steg():
    """Sista steget tappas — något går aldrig att låsa upp."""
    äkta = d.stege
    d.stege = lambda språk, ordklass="Verb": äkta(språk, ordklass)[:-1]
    return lambda: setattr(d, "stege", äkta)


def _sabotage_kort_per_cell():
    """Före hopslagningen: ett ändelsekort per CELL, inte per ändelse."""
    # VIA sys.modules: `sprakprog.kort.befolka` löser upp till FUNKTIONEN,
    # eftersom `kort/__init__.py` återexporterar den och skuggar submodulen.
    import sprakprog.kort.befolka          # noqa: F401  (registrerar modulen)
    b = sys.modules["sprakprog.kort.befolka"]
    global _CACHE
    äkta_cache, _CACHE = _CACHE, None
    äkta = b._lägg_till
    def per_cell(kort, typ, språk, facit, **kw):
        if typ == "system":
            kw["cell"] = kw.pop("egenskap", None) and None
            kw["cell"] = kw.get("cell") or f"cell{len(kort)}"
        return äkta(kort, typ, språk, facit, **kw)
    b._lägg_till = per_cell
    def ångra():
        global _CACHE
        b._lägg_till = äkta
        _CACHE = äkta_cache
    return ångra


def _sabotage_hoppa_celler():
    """Grinda bort celler i stället för att slå ihop dem — hålet återinfört.

    Det VAR det andra alternativet: låta böjningsstegen utelämna celler vars
    ändelse redan lärts ut. Då försvinner kortet för `K0/pres_3sg`, och
    meningen `Elle parle.` slår upp en cell utan kort.
    """
    import sprakprog.kort.befolka                # noqa: F401
    b = sys.modules["sprakprog.kort.befolka"]
    global _CACHE
    äkta_cache, _CACHE = _CACHE, None
    äkta = b._lägg_till
    tappade: set = set()

    def hoppa(kort, typ, språk, facit, **kw):
        # TAPPA DET FÖRSTA kortet per (språk, klass), inte dubbletterna.
        #
        # Första försöket hoppade över dubbletterna — men efter hopslagningen
        # FINNS inga dubbletter, så sabotaget tog bort ingenting och provet
        # såg stumt ut. Invarianten handlar om att varje ändelse HAR ett
        # kort, och det enda som bryter den är ett kort som saknas.
        if typ == "system":
            nyckel = (språk, kw.get("ordklass"), kw.get("klass"))
            if nyckel not in tappade:
                tappade.add(nyckel)
                return None
        return äkta(kort, typ, språk, facit, **kw)

    b._lägg_till = hoppa

    def ångra():
        global _CACHE
        b._lägg_till = äkta
        _CACHE = äkta_cache
    return ångra


def _sabotage_utan_migration():
    """Före migrationen: gamla cell-nycklade kort lämnades kvar."""
    import sprakprog.kort.befolka                # noqa: F401
    b = sys.modules["sprakprog.kort.befolka"]
    äkta = b._slå_ihop_gamla_ändelsekort
    b._slå_ihop_gamla_ändelsekort = lambda *a, **kw: 0
    return lambda: setattr(b, "_slå_ihop_gamla_ändelsekort", äkta)


def _sabotage_grundböjning_utspridd():
    """Före hopklumpningen: ett steg per cell, även i grundböjningen."""
    äkta = d.grundböjning
    d.grundböjning = lambda språk, ordklass="Verb": frozenset()
    return lambda: setattr(d, "grundböjning", äkta)


#: (sabotage, vilket prov det ska fälla).
SABOTAGE = [
    (_sabotage_omkastad, 0),
    (_sabotage_utan_filter, 1),
    (_sabotage_halva, 2),
    (_sabotage_utan_filter, 3),
    (_sabotage_tappa_steg, 4),
    (_sabotage_utan_beroenden, 5),
    (_sabotage_två_block, 6),
    (_sabotage_kort_per_cell, 7),
    (_sabotage_hoppa_celler, 8),
    (_sabotage_utan_migration, 9),
    (_sabotage_grundböjning_utspridd, 10),
]


def main() -> int:
    print("projektionen av den universella cellistan\n")
    p = d.projicera()
    print(f"  {len(d.universella_celler())} universella celler → "
          + ", ".join(f"{s}:{len(v)}" for s, v in sorted(p.items())) + "\n")
    fel = 0
    for namn, prov in PROV:
        rader = prov()
        fel += bool(rader)
        print(f"  {'✓' if not rader else '✗'} {namn}")
        for r in rader[:4]:
            print(f"      {r}")
        if len(rader) > 4:
            print(f"      … och {len(rader) - 4} till")

    print("\nfalsifiering — varje invariant mot sitt eget sabotage:")
    stumma = []
    for sabotera, i in SABOTAGE:
        namn, prov = PROV[i]
        ångra = sabotera()
        try:
            höll = not prov()
        finally:
            ångra()
        if höll:
            stumma.append(namn)
        print(f"  {'✗ STUM' if höll else '✓ föll'}  {namn}"
              f"  ← {sabotera.__doc__.splitlines()[0]}")

    print(f"\n{len(PROV)} invarianter, {fel} brott, {len(stumma)} stumma.")
    return 1 if fel or stumma else 0


if __name__ == "__main__":
    raise SystemExit(main())
