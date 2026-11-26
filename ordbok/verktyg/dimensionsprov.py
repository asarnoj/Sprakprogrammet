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
        # TYPEN SÄGER INTE LÄNGRE VAD ETT STEG BÄR. Sedan en konstruktion
        # slås ihop med den böjning den kräver innehåller ett
        # `konstruktion`-steg både konstruktionsnamnet och celler. Provet
        # räknar därför på UNIONEN av alla namn och inte per typ — annars
        # mäter det den gamla formen och faller på rätt data.
        alla = [n for _, namn in s for n in namn]
        # DE NÅBARA CELLERNA, inte alla projicerade. Stegen utelämnar celler
        # ingen spec kan producera — franskans konditionalis, tyskans
        # konjunktiv — eftersom en nivå för dem låser upp ingenting. Att
        # kräva dem här vore att kräva tomma nivåer.
        nåbart = d.nåbara_celler(språk)
        väntat = sorted([*NIVÅ.values(),
                         *(c for c, _ in d.projicera().get(språk, [])
                           if c in nåbart)])
        if sorted(alla) != väntat:
            saknas = set(väntat) - set(alla)
            extra = set(alla) - set(väntat)
            fel.append(f"{språk}: stegen är inte hel — {len(saknas)} saknas, "
                       f"{len(extra)} tillkom")
        if len(set(alla)) != len(alla):
            fel.append(f"{språk}: något förekommer två gånger i stegen")
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


def prov_grundböjningen_först() -> list[str]:
    """Ingenting får ligga före grundböjningen.

    ERSATTE "de två sorterna varvas", och det var rätt att ersätta den.
    Flätningen skulle hindra att stegen blev två block efter varandra, men
    sedan konstruktionerna slås ihop med sin böjning ligger cellerna INUTI
    konstruktionsstegen — och då är få typbyten inte längre ett symptom utan
    designen. Provet mätte en form systemet vuxit ur.

    Det som fortfarande gäller, och som allt hänger på: nivå 1 måste gå att
    tala på. Ligger en konstruktion före grundböjningen har kursen en nivå
    utan verbform, och det var hela skälet att grundböjningen bröts ut.
    """
    fel = []
    for språk in SPRÅK:
        steg = d.stege(språk)
        grund = d.grundböjning(språk)
        if not grund:
            continue
        först = next((i for i, (typ, namn) in enumerate(steg)
                      if typ == "böjning" and set(namn) & grund), None)
        if först is None:
            fel.append(f"{språk}: grundböjningen finns inte i stegen")
        elif först != 0:
            fel.append(f"{språk}: grundböjningen ligger på steg {först + 1}, "
                       f"inte först — nivå 1 saknar verbform")
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


def prov_ingen_stam_är_sitt_ord() -> list[str]:
    """Ett stamkort får aldrig ha samma facit som sitt eget ordkort.

    SAMMA TOMMA LÄROMOMENT SOM ÄNDELSERNA HADE, i en annan korttyp. Julius:
    *"Vi gjorde il i ordglosdelen redan. Är det problematiskt att il är
    identisk som ord och som stem?"* — och det är det: kortet frågar samma
    sak med samma svar, och den som klarat ordet kan stammen utan att veta
    om det.

    Mätt på franskan innan villkoret sattes in: 141 av 216 stamkort hade
    exakt sitt ordkorts facit — Substantiv 133 av 136, Pronomen 8 av 10,
    Verb 0 av 70. Verben är undantaget och det är just där stammen bär
    betydelse: `exist` mot `exister`. För ett oböjt substantiv finns ingen
    stam att skilja från ordet.

    LÄSER `härled`, INTE DEN BEFOLKADE DATABASEN. Gjorde den det blev provet
    stumt: migrationen städar bort korten efter insättningen, så ett brott i
    HÄRLEDNINGEN syntes inte i beståndet. Invarianten gäller regeln — vilka
    kort som skapas — och migrationen har sitt eget prov.
    """
    from sprakprog.db import anslut
    from sprakprog.kort.befolka import härled
    sdb = anslut()
    fel = []
    for s_ in sorted(SPRÅK):
        rader = härled(sdb, {s_}, None, None)
        ord_ = {(r[3], r[4]): r[10] for r in rader if r[1] == "ord"}
        for r in rader:
            if r[1] == "stam" and ord_.get((r[3], r[4])) == r[10]:
                fel.append(f"{s_}/{r[3]}: stamkortet {r[10]!r} är sitt eget "
                           f"ordkort")
    return fel[:6]


def prov_cellen_tappar_inte_ordet() -> list[str]:
    """Ingen cell får ha ENBART sitt ändelsekort i beroendekartan.

    DET FARLIGA MED ATT TA BORT STAMKORTET, och nästan det fel jag gjorde:
    `härled` slutade skapa kortet men `_cellkort` pekade fortfarande på det,
    och raden föll bort tyst vid insättningen (`if n in idn`). Kvar i cellen
    blev bara ÄNDELSEN. Ett felstavat `mère` hade då bokförts som att
    ändelsen `s` brast.

    Mätt på beroendekartan i det läget: fr 811 av 8 874 celler, de 13 177 av
    23 109, sv 2 366, en 1 593. Ordkorten hade samtidigt NOLL rader i
    `Cellkort` i samtliga språk — stamkortet stod och höll ordets plats.
    Rättningen är att cellen pekar på ordkortet i stället: samma kort som
    förr, med sitt riktiga namn.
    """
    from sprakprog.db import anslut
    from sprakprog.kort.befolka import _cellkort, härled
    sdb = anslut()
    fel = []
    for s_ in sorted(SPRÅK):
        nycklar = {r[0] for r in härled(sdb, {s_}, None, None)}
        per: dict[tuple, set[str]] = {}
        for a, b_, c, cell, n in _cellkort(sdb, {s_}):
            if n in nycklar:
                per.setdefault((a, b_, c, cell), set()).add(n.split(":")[0])
        naken = [k for k, v in per.items() if v <= {"system"}]
        if naken:
            fel.append(f"{s_}: {len(naken)} celler utan annat kort än "
                       f"ändelsen, t.ex. {naken[0][1]}/{naken[0][3]}")
    return fel


def prov_stammigrationen_bevarar_historiken() -> list[str]:
    """Ett stamkort som ÄR sitt ord ska föras över till ordkortet.

    Samma hot som vid ändelsehopslagningen och samma svar: korten blir inte
    fel när regeln ändras, de blir OSYNLIGA — kvar med sin historik, utan
    rad i `Cellkort`, omöjliga att nå. Historiken hör hemma på ordkortet,
    för de två korten mätte samma kunskap under två namn.
    """
    import tempfile
    from sprakprog.db import anslut
    from sprakprog.kort.befolka import befolka
    from sprakprog.kort.db import skapa_kortdatabas
    db = skapa_kortdatabas(Path(tempfile.mkdtemp()) / "stam.db")
    db.execute(
        """INSERT INTO Kort (nyckel, typ, språk, koncept, ordklass, klass,
                             stamgrupp, facit, räckvidd, stabilitet, svårighet,
                             tillstånd, sedd, förfaller, antal, fall)
           VALUES ('stam:fr:fam_mamma::Substantiv:K0::0:', 'stam', 'fr',
                   'fam_mamma', 'Substantiv', 'K0', 0, 'mère', 2, 3.5, 5.0,
                   2, '2026-08-01T09:00:00+00:00',
                   '2026-08-20T09:00:00+00:00', 4, 1)""")
    gammalt = db.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    db.execute("""INSERT INTO Repetition (kort_id, tidpunkt, betyg)
                  VALUES (?, '2026-08-01T09:00:00+00:00', 3)""", (gammalt,))
    db.commit()
    befolka(db, anslut(), {"fr"}, cefr="C2", mät=False)

    fel = []
    if db.execute("SELECT 1 FROM Kort WHERE id = ?", (gammalt,)).fetchone():
        fel.append("stamkortet står kvar trots att det är sitt eget ord")
    rad = db.execute(
        "SELECT kort_id FROM Repetition WHERE tidpunkt = '2026-08-01T09:00:00+00:00'"
    ).fetchone()
    if rad is None:
        fel.append("repetitionsraden försvann med kortet")
    else:
        ny = db.execute("SELECT typ, facit FROM Kort WHERE id = ?",
                        (rad["kort_id"],)).fetchone()
        if ny is None:
            fel.append("repetitionsraden pekar på ett kort som inte finns")
        elif not (ny["typ"] == "ord" and ny["facit"] == "mère"):
            fel.append(f"historiken hamnade på fel kort: {dict(ny)}")
    db.close()
    return fel


def prov_ändelsen_finns_i_formen() -> list[str]:
    """En cell får bara peka på ett ändelsekort om formen HAR ändelsen.

    Julius om `J'ai.`: *"vad är ens s för ändelsekort? Prövades det
    verkligen?"* — nej. K1:s `pres_1sg` är `s`, men `ai` är suppletiv och
    innehåller inget `s`. Kortet fick ändå ✓.

    `dela_upp` gör redan rätt: en form som inte slutar på klassens ändelse
    blir en REST med eget formkort. `_cellkort` körde ändelseslingan för båda
    radtyperna och kopplade alltså in resterna igen. Mätt på kopplingarna:

        ja 8,9 %   fr 6,2 %   en 5,8 %   it 5,4 %   es 3,5 %   sv 1,7 %

            was     → ändelsekort 'ed'
            です     → ändelsekort 'ます'
            mannen  → ändelsekort 'et'

    Kortet steg i stabilitet på bevis som aldrig fanns — den enda feltypen
    som FÖRDÄRVAR data i stället för att sakna den (D3).

    PROVET LÄSER FORMEN, inte bara radtypen. Resten bär hela ordformen i
    `stammar.tsv`, så påståendet går att pröva mot strängen: ändelsen får
    inte vara ett suffix av formen (det är vad som gjorde den till en rest),
    och ingen systemkoppling får utgå från raden.
    """
    from sprakprog.db import anslut
    from sprakprog.kort.befolka import _cellkort, _stamrader, _ändelserader
    sdb = anslut()
    fel = []
    for s_ in sorted(SPRÅK):
        änd = {(r["språk"], r["ordklass"], r["klass"], r["cell"]):
               r["ändelse"] or "∅" for r in _ändelserader({s_})}
        rester = {}
        for rad in _stamrader({s_}):
            if int(rad["stamgrupp"]) < 0:
                for cell in rad["celler"].split(","):
                    rester[(rad["språk"], rad["koncept"],
                            rad["variant"] or None, cell)] = rad
        # a) premissen: en rest uppvisar inte klassens ändelse
        for nyckel, rad in rester.items():
            e = änd.get((rad["språk"], rad["ordklass"], rad["klass"], nyckel[3]))
            if e is not None and e != "∅" and rad["form"].endswith(e):
                fel.append(f"{s_}/{nyckel[1]}/{nyckel[3]}: {rad['form']!r} "
                           f"slutar på {e!r} men räknades som rest")
        # b) slutsatsen: ingen systemkoppling utgår från en rest
        träffar = [(k, n) for *k4, n in
                   [(a, b, c, d, n) for a, b, c, d, n in _cellkort(sdb, {s_})]
                   for k in [tuple(k4)] if n.startswith("system:") and k in rester]
        if träffar:
            k, n = träffar[0]
            fel.append(f"{s_}: {len(träffar)} rester kopplade till ett "
                       f"ändelsekort, t.ex. {rester[k]['form']!r} → {n}")
    return fel[:6]


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
        ("grundböjningen ligger först", prov_grundböjningen_först),
        ("inget tomt läromoment", prov_inget_tomt_läromoment),
        ("varje cell har ett kort", prov_varje_cell_har_ett_kort),
        ("migrationen bevarar historiken", prov_migrationen_bevarar_historiken),
        ("nivå 1 går att tala på", prov_nivå_ett_går_att_tala_på),
        # NYA PROV LÄGGS SIST. `SABOTAGE` pekar på INDEX i den här listan, så
        # varje insättning i mitten flyttar tystnaden till ett annat prov än
        # det sabotaget skrevs för. Jag sköt själv "nivå 1" från 10 till 13.
        ("ingen stam är sitt eget ord", prov_ingen_stam_är_sitt_ord),
        ("cellen tappar inte ordet", prov_cellen_tappar_inte_ordet),
        ("stammigrationen bevarar historiken",
         prov_stammigrationen_bevarar_historiken),
        ("ändelsen finns i formen", prov_ändelsen_finns_i_formen)]



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


def _sabotage_konstruktioner_först():
    """Alla konstruktioner före all böjning — nivå 1 utan verbform."""
    äkta = d.stege
    def block(språk, ordklass="Verb"):
        s = äkta(språk, ordklass)
        return ([x for x in s if x[0] == "konstruktion"]
                + [x for x in s if x[0] == "böjning"])
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


def _sabotage_behåll_identiska_stammar():
    """Före villkoret: stamkortet skapades även när stammen var hela ordet."""
    import sprakprog.kort.befolka                # noqa: F401
    global _CACHE
    äkta_cache, _CACHE = _CACHE, None
    b = sys.modules["sprakprog.kort.befolka"]
    äkta = b._lemman
    b._lemman = lambda *a, **kw: {}
    def ångra():
        global _CACHE
        b._lemman = äkta
        _CACHE = äkta_cache
    return ångra


def _sabotage_utan_omdirigering():
    """Före omdirigeringen: cellen pekade på stamkortet som inte skapas."""
    import sprakprog.kort.befolka                # noqa: F401
    b = sys.modules["sprakprog.kort.befolka"]
    äkta_cellkort, äkta_lemman = b._cellkort, b._lemman

    def utan(språk_db, språk):
        # Bygger kartan som förr genom att dölja lemmana FÖR KARTAN men inte
        # för `härled`: stamnyckeln emitteras, kortet finns inte, raden faller.
        b._lemman = lambda *a, **kw: {}
        try:
            return äkta_cellkort(språk_db, språk)
        finally:
            b._lemman = äkta_lemman

    b._cellkort = utan

    def ångra():
        b._cellkort, b._lemman = äkta_cellkort, äkta_lemman
    return ångra


def _sabotage_utan_stammigration():
    """Före migrationen: gamla stamkort lämnades kvar med sin historik."""
    import sprakprog.kort.befolka                # noqa: F401
    b = sys.modules["sprakprog.kort.befolka"]
    äkta = b._slå_ihop_stam_med_ord
    b._slå_ihop_stam_med_ord = lambda *a, **kw: 0
    return lambda: setattr(b, "_slå_ihop_stam_med_ord", äkta)


def _sabotage_ändelse_även_på_rest():
    """Före villkoret: ändelseslingan kördes för rester också.

    Uttryckt som ett TILLÄGG till den riktiga kartan i stället för som en
    kopia av den gamla koden — annars prövar sabotaget sin egen avskrift.
    """
    import sprakprog.kort.befolka                # noqa: F401
    b = sys.modules["sprakprog.kort.befolka"]
    äkta = b._cellkort

    def med_rester(språk_db, språk):
        ut = list(äkta(språk_db, språk))
        änd = {(r["språk"], r["ordklass"], r["klass"], r["cell"]):
               r["ändelse"] or "∅" for r in b._ändelserader(språk)}
        for rad in b._stamrader(språk):
            if int(rad["stamgrupp"]) >= 0:
                continue
            for cell in rad["celler"].split(","):
                e = änd.get((rad["språk"], rad["ordklass"], rad["klass"], cell))
                if e is None:
                    continue
                ut.append((rad["språk"], rad["koncept"], rad["variant"] or None,
                           cell, b._nyckel("system", rad["språk"], None, None,
                                           rad["ordklass"], rad["klass"],
                                           None, None, e)))
        return ut

    b._cellkort = med_rester
    return lambda: setattr(b, "_cellkort", äkta)


#: (sabotage, vilket prov det ska fälla).
SABOTAGE = [
    (_sabotage_omkastad, 0),
    (_sabotage_utan_filter, 1),
    (_sabotage_halva, 2),
    (_sabotage_utan_filter, 3),
    (_sabotage_tappa_steg, 4),
    (_sabotage_utan_beroenden, 5),
    (_sabotage_konstruktioner_först, 6),
    (_sabotage_kort_per_cell, 7),
    (_sabotage_hoppa_celler, 8),
    (_sabotage_utan_migration, 9),
    (_sabotage_grundböjning_utspridd, 10),
    (_sabotage_behåll_identiska_stammar, 11),
    (_sabotage_utan_omdirigering, 12),
    (_sabotage_utan_stammigration, 13),
    (_sabotage_ändelse_även_på_rest, 14),
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
