"""Svenska böjningsregler — steg 0, KÄRNAN 3.4.

Reglerna är skrivna ur standardgrammatik och inte härledda ur datan, just för
att de ska kunna prövas MOT datan. Varje `förutsäg` tar ordets grundform och
de former som redan är kort för ordet, och förutsäger resten. None betyder att
reglerna inte kan förutsäga cellen; finns cellen blir den då ett kort.

KORTEN, OCH VAR DE SYNS HÄR

  ändelse       klassens ändelser, skrivna direkt i förutsägelsen
                  verb 1   -ar  -ade      -at    arbeta
                  verb 2   -er  -de/-te   -t     köpa, ringa
                  verb 3   -r   -dde      -tt    tro
  regel         ljudanpassningar, loggade med namn i `Spår` (LJUDREGLER)
  oregelbunden  det förutsägelsen missar — hittas av kontrollen, inte här

STANDARDKLASSEN ÄR DEN PRODUKTIVA. Ett verb på -a böjs som `arbeta` tills ett
kort visar något annat, eftersom nya verb blir ar-verb (googla → googlar →
googlade). Presens är den första form som visar klassen: `köper` blir kortet,
och därefter följer `köpte`, `köpt` och `köps` av reglerna.

PRETERITUM BÄR RESTEN AV ETT SVAGT VERB. Supinum och particip räknas ur
preteritum och inte ur stammen, så de oregelbundna svaga verben följer av ett
enda kort: `gjorde` → `gjort`, `gjord`, `gjorda`.

STARKA VERB FÅR PRETERITUM OCH SUPINUM SOM KORT. Om supinum ablautar
(`sprungit`) eller inte (`skrivit`) syns inte i ordet, och principen väljer då
det försiktiga. Participen följer av supinum: `sprungit` → `sprungen`.

Där ett val är tveksamt står det i GRANSKA längst ner.
"""

from __future__ import annotations

from . import Ordklass, Spår

NAMN = "svenska"

VOKAL = frozenset("aeiouyåäöé")
TONLÖS = frozenset("kpstx")
UTRUM, NEUTRUM = 1, 2


# ── ljudregler ───────────────────────────────────────────────────────────

LJUDREGLER = {
    "mm_nn_före_konsonant": "m och n dubbeltecknas inte före konsonant: känn + de → kände, komm + na → komna",
    "mm_i_ordslut": "m dubbeltecknas inte i ordslut: glömm → glöm (men känn)",
    "konsonant_dt_tar_e": "stam på konsonant + d/t tar bara -e i preteritum: använd → använde, lyft → lyfte",
    "s_x_tar_es": "stam på s eller x tar -es i presens passiv: läs → läses",
    "obetonat_e_faller": "e i obetonat -el/-er/-en faller före ändelse: fågel → fåglar, öppen → öppna",
    "en_blir_et": "adjektiv på obetonat -en tar -et i neutrum: öppen → öppet",
    "d_blir_t": "d blir t i neutrum: hård → hårt, röd → rött",
    "vokal_t_blir_tt": "vokal + t dubbeltecknas i neutrum: vit → vitt",
    "slutvokal_tar_tt": "adjektiv på vokal tar -tt i neutrum: ny → nytt",
    "sam_dubblar_m": "-sam dubbeltecknar m före ändelse: ensam → ensamma",
}


def _före_konsonant(stam: str, spår: Spår) -> str:
    if stam.endswith(("mm", "nn")) and spår("mm_nn_före_konsonant"):
        return stam[:-1]
    return stam


def _ordslut(stam: str, spår: Spår) -> str:
    if stam.endswith("mm") and spår("mm_i_ordslut"):
        return stam[:-1]
    return stam


def _stavelser(ord: str) -> int:
    """Antal vokalgrupper — tillräckligt för att skilja sten från vatten."""
    antal, föregående = 0, False
    for tecken in ord:
        vokal = tecken in VOKAL
        antal += vokal and not föregående
        föregående = vokal
    return antal


def _obetonat_slut(bas: str) -> bool:
    """-el, -er, -en efter konsonant i flerstaviga ord: fågel, vatten, öppen.
    Enstaviga ord har ingen obetonad slutstavelse: sten, ren."""
    return (_stavelser(bas) >= 2 and bas[-2:] in ("el", "er", "en")
            and bas[-3] not in VOKAL)


# ── verb ─────────────────────────────────────────────────────────────────

VERBORDNING = ("pres", "pret", "sup", "perfpart_obest_utr_sg",
               "perfpart_obest_neu_sg", "perfpart_a", "imp",
               "inf_passiv", "pres_passiv", "pret_passiv", "sup_passiv")


def _verbbas(facit: dict, lexem) -> tuple[dict, dict]:
    """Grundformen är infinitiven. Partikel och objekt i lemmat följer med
    varje form ("håller med") och skalas av; "sig" står inte i formerna."""
    huvud, _, rest = lexem["lemma"].partition(" ")
    svans = "" if rest in ("", "sig") else " " + rest
    norm = {}
    for cell, form in facit.items():
        if form:
            norm[cell] = form[:-len(svans)] if svans and form.endswith(svans) else form
    if norm.get("inf"):
        bas = norm["inf"]
    elif norm.get("inf_passiv", "").endswith("s"):
        bas = norm["inf_passiv"][:-1]        # deponens: hoppas → hoppa
    else:
        bas = huvud
    return {"bas": bas}, norm


def _svag_pret(stam: str, spår: Spår) -> str:
    s = _före_konsonant(stam, spår)
    if len(s) >= 2 and s[-1] in "dt" and s[-2] not in VOKAL and spår("konsonant_dt_tar_e"):
        return s + "e"
    return s + ("te" if s[-1] in TONLÖS else "de")


def _sup_ur_pret(pret: str) -> str | None:
    if pret.endswith("tte"):
        return pret[:-1]                      # bytte → bytt
    if pret.endswith("dde"):
        return pret[:-3] + "tt"               # trodde → trott
    if pret.endswith(("de", "te")):
        return pret[:-2] + "t"                # arbetade → arbetat, köpte → köpt
    return None                               # starkt preteritum


def verb(info: dict, k: dict, spår: Spår) -> dict:
    inf = info["bas"]
    stam = inf[:-1] if inf.endswith("a") else inf
    ut: dict[str, str | None] = {}

    spår.cell = "pres"
    if "pres" in k:
        pres = k["pres"]
    elif "pres_passiv" in k:                  # deponens: klassen syns i s-formen
        s = k["pres_passiv"]
        pres = (s[:-2] if s.endswith("es") else s[:-1]) + "er"
    else:
        pres = inf + "r"
    ut["pres"] = pres
    klass2 = pres == stam + "er" or (stam.endswith("r") and pres == stam)
    # Klassen syns i presens, den form som visar den (3.4).
    klass = "er" if klass2 else ("ar" if inf.endswith("a") else "kortverb")
    if "pres" not in k:
        spår.ändelse(klass)

    spår.cell = "imp"
    ut["imp"] = (_ordslut(pres[:-2] if pres.endswith("er") else pres, spår)
                 if klass2 else inf)
    spår.ändelse(klass)

    spår.cell = "pret"
    if "pret" in k:
        pret = k["pret"]
    elif "pret_passiv" in k:
        pret = k["pret_passiv"][:-1]
    elif klass2:
        pret = _svag_pret(stam, spår)
        spår.ändelse(klass)
    else:
        pret = inf + ("de" if inf.endswith("a") else "dde")
        spår.ändelse(klass)
    ut["pret"] = pret

    spår.cell = "sup"
    if "sup" in k:
        sup = k["sup"]
    elif "sup_passiv" in k:
        sup = k["sup_passiv"][:-1]
    else:
        sup = _sup_ur_pret(pret)
        if sup is not None:
            spår.ändelse(klass)
    ut["sup"] = sup

    spår.cell = "perfpart_obest_utr_sg"
    particip = ("perfpart_obest_utr_sg", "perfpart_obest_neu_sg", "perfpart_a")
    utr = k.get("perfpart_obest_utr_sg")
    if utr is not None and utr.endswith("en"):
        bas = utr[:-2]
        neu, a = bas + "et", _före_konsonant(bas, spår) + "na"
        spår.ändelse("stark", *particip[1:])
    elif utr is not None:
        neu, a = sup, utr + "a"
        spår.ändelse(klass, *particip[1:])
    elif sup and sup.endswith("it"):
        bas = sup[:-2]
        utr, neu, a = bas + "en", bas + "et", _före_konsonant(bas, spår) + "na"
        spår.ändelse("stark", *particip)
    elif pret.endswith(("de", "te")):
        utr = pret[:-1]
        neu, a = sup, (pret if pret.endswith("ade") else utr + "a")
        spår.ändelse(klass, *particip)
    else:
        utr = neu = a = None
    ut.update({"perfpart_obest_utr_sg": utr, "perfpart_obest_neu_sg": neu,
               "perfpart_a": a})

    spår.cell = "pres_passiv"
    if klass2:
        imp = ut["imp"]
        if imp.endswith(("s", "x")) and spår("s_x_tar_es"):
            pres_passiv = imp + "es"
        else:
            pres_passiv = imp + "s"
    else:
        pres_passiv = inf + "s"
    spår.ändelse(klass)
    ut.update({"inf_passiv": inf + "s", "pres_passiv": pres_passiv,
               "pret_passiv": pret + "s" if pret else None,
               "sup_passiv": sup + "s" if sup else None})
    # S-passiven av infinitiv, preteritum och supinum är samma -s i alla klasser.
    spår.ändelse("alla", "inf_passiv", "pret_passiv", "sup_passiv")
    ut.update(k)
    return ut


def _verbdatafel(facit: dict, info: dict) -> dict:
    """Passiv är aktiv form plus -s i infinitiv, preteritum och supinum,
    utan undantag. En form som bryter mot det är ett fel i datan."""
    ut = {}
    for passiv, aktiv in (("inf_passiv", "inf"), ("pret_passiv", "pret"),
                          ("sup_passiv", "sup")):
        if facit.get(passiv) and facit.get(aktiv) and facit[passiv] != facit[aktiv] + "s":
            ut[passiv] = f"passiv ≠ aktiv form + s ({facit[aktiv]} → {facit[aktiv]}s)"
    if facit.get("pres_passiv") and not facit["pres_passiv"].endswith("s"):
        ut["pres_passiv"] = "passiv utan -s"
    return ut


# ── substantiv ───────────────────────────────────────────────────────────

SUBSTORDNING = ("best_sg_ack_dat_nom", "obest_pl_ack_dat_nom", "best_pl_ack_dat_nom",
                "obest_sg_gen", "best_sg_gen", "obest_pl_gen", "best_pl_gen")
GENITIV_AV = {"obest_sg_gen": "obest_sg_ack_dat_nom", "best_sg_gen": "best_sg_ack_dat_nom",
              "obest_pl_gen": "obest_pl_ack_dat_nom", "best_pl_gen": "best_pl_ack_dat_nom"}

# Suffix som entydigt ger plural på -er. Se GRANSKA.
ER_SUFFIX = ("het", "tion", "sion", "ist", "ent", "ant", "är", "ör", "or",
             "ur", "in", "ik", "at", "é")


def _genitiv(form: str) -> str:
    return form if form.endswith(("s", "x", "z")) else form + "s"


def _substbas(facit: dict, lexem) -> tuple[dict, dict]:
    norm = {c: f for c, f in facit.items() if f}
    sg = norm.get("obest_sg_ack_dat_nom")
    bas = sg or norm.get("obest_pl_ack_dat_nom") or lexem["lemma"]
    return {"bas": bas, "genus": lexem["genus"], "tantum": not sg}, norm


def substantiv(info: dict, k: dict, spår: Spår) -> dict:
    bas, genus, tantum = info["bas"], info["genus"], info["tantum"]
    ut: dict[str, str | None] = {}

    spår.cell = "best_sg_ack_dat_nom"
    if genus == NEUTRUM:
        if bas[-1] in VOKAL:
            best = bas + "t"
            spår.ändelse("neutrum_vokal")
        elif _obetonat_slut(bas) and spår("obetonat_e_faller"):
            best = _före_konsonant(bas[:-2], spår) + bas[-1] + "et"
            spår.ändelse("neutrum")
        else:
            best = bas + "et"
            spår.ändelse("neutrum")
    elif bas[-1] in VOKAL or _obetonat_slut(bas) or (len(bas) > 3 and bas.endswith("or")):
        best = bas + "n"
        spår.ändelse("utrum_n")
    else:
        best = bas + "en"
        spår.ändelse("utrum")
    best = k.get("best_sg_ack_dat_nom", best)
    ut["best_sg_ack_dat_nom"] = best

    spår.cell = "obest_pl_ack_dat_nom"
    if tantum:
        pl = bas
    elif genus == NEUTRUM:
        if bas.endswith("eri"):
            pl = bas + "er"                        # bagerier
            spår.ändelse("neutrum_eri")
        elif bas[-1] in VOKAL:
            pl = bas + "n"                         # äpplen
            spår.ändelse("neutrum_vokal")
        else:
            pl = bas                               # hus
            spår.ändelse("neutrum")
    elif bas.endswith("are"):
        pl = bas                                   # lärare
        spår.ändelse("are")
    elif bas.endswith("else"):
        pl = bas + "r"                             # upplevelser
        spår.ändelse("else")
    elif bas.endswith(("ing", "dom")):
        pl = bas + "ar"                            # klänningar, sjukdomar
        spår.ändelse("ing_dom")
    elif bas.endswith("a"):
        pl = bas[:-1] + "or"                       # flickor
        spår.ändelse("a")
    elif bas.endswith("e"):
        pl = bas[:-1] + "ar"                       # pojkar
        spår.ändelse("e")
    elif _obetonat_slut(bas) and spår("obetonat_e_faller"):
        pl = _före_konsonant(bas[:-2], spår) + bas[-1] + "ar"   # fåglar
        spår.ändelse("obetonat_slut")
    elif bas.endswith(ER_SUFFIX):
        pl = bas + "er"
        spår.ändelse("suffix_er")
    else:
        pl = None
    pl = k.get("obest_pl_ack_dat_nom", pl)
    ut["obest_pl_ack_dat_nom"] = pl

    spår.cell = "best_pl_ack_dat_nom"
    if pl is None:
        bestpl = None
    elif tantum and pl.endswith("r"):
        bestpl = pl + "na"
        spår.ändelse("tantum_r")
    elif genus == UTRUM and pl == bas and bas.endswith("are"):
        bestpl = bas[:-1] + "na"                   # lärarna
        spår.ändelse("are")
    elif pl.endswith("on"):
        bestpl = pl + "en"                         # ögonen
        spår.ändelse("on")
    elif genus == NEUTRUM and not tantum and pl == bas and best.endswith("et"):
        bestpl = best[:-2] + "en"                  # husen, rummen
        spår.ändelse("neutrum")
    elif pl.endswith("r"):
        bestpl = pl + "na"
        spår.ändelse("r")
    elif pl.endswith("n"):
        bestpl = pl + "a"                          # ansiktena
        spår.ändelse("n")
    else:
        bestpl = pl + "en"                         # mössen
        spår.ändelse("övrig")
    ut["best_pl_ack_dat_nom"] = k.get("best_pl_ack_dat_nom", bestpl)

    for gen, nom in GENITIV_AV.items():
        spår.cell = gen
        ut[gen] = _genitiv(ut[nom]) if ut.get(nom) else (_genitiv(bas) if nom == "obest_sg_ack_dat_nom" else None)
        if ut[gen] is not None:
            spår.ändelse("efter_s_x_z" if ut[gen] == (ut.get(nom) or bas) else "genitiv")
    ut.update(k)
    return ut


def _substdatafel(facit: dict, info: dict) -> dict:
    """Två samband utan undantag: genitiven är formen plus -s (utan -s efter
    s, x, z), och bestämd singular slutar på -n i utrum och -t i neutrum."""
    ut = {}
    for gen, nom in GENITIV_AV.items():
        if facit.get(gen) and facit.get(nom) and facit[gen] != _genitiv(facit[nom]):
            ut[gen] = f"genitiv ≠ form + s ({facit[nom]} → {_genitiv(facit[nom])})"
    best, genus = facit.get("best_sg_ack_dat_nom"), info["genus"]
    if best and genus in (UTRUM, NEUTRUM) and not best.endswith("n" if genus == UTRUM else "t"):
        ut["best_sg_ack_dat_nom"] = ("bestämd form stämmer inte med genus "
                                     f"({'utrum' if genus == UTRUM else 'neutrum'} i datan)")
        if facit.get("best_sg_gen"):
            ut.setdefault("best_sg_gen", "följer av bestämd singular, som är misstänkt fel")
    return ut


# ── adjektiv ─────────────────────────────────────────────────────────────

ADJORDNING = ("obest_f_sg_pos", "obest_a_pl_pos", "best_a_sg_pos", "best_a_pl_pos",
              "komp", "obest_superl", "best_superl")


def _adjbas(facit: dict, lexem) -> tuple[dict, dict]:
    norm = {c: f for c, f in facit.items() if f}
    return {"bas": norm.get("obest_m_sg_pos") or lexem["lemma"]}, norm


def _neutrum(bas: str, spår: Spår) -> str:
    if bas.endswith("en") and _obetonat_slut(bas) and spår("en_blir_et"):
        spår.ändelse("t")
        return bas[:-1] + "t"                      # öppet, litet
    if bas.endswith("ad") and _stavelser(bas) >= 2:
        spår.ändelse("ad")
        return bas[:-1] + "t"                      # förvånat, men glad → glatt
    if bas.endswith("dd") and spår("d_blir_t"):
        spår.ändelse("t")
        return bas[:-2] + "tt"                     # rädd → rätt
    if bas.endswith("tt"):
        spår.ändelse("tt")
        return bas                                 # lätt, trött
    if bas.endswith("d") and spår("d_blir_t"):
        spår.ändelse("t")
        return bas[:-1] + ("tt" if bas[-2] in VOKAL else "t")   # rött, hårt
    if bas.endswith("t"):
        if bas[-2] in VOKAL and spår("vokal_t_blir_tt"):
            spår.ändelse("t")
            return bas + "t"                       # vitt
        spår.ändelse("konsonant_t")
        return bas                                 # svart
    if bas.endswith("nn") and spår("mm_nn_före_konsonant"):
        spår.ändelse("t")
        return bas[:-1] + "t"                      # tunt
    if bas[-1] in VOKAL and spår("slutvokal_tar_tt"):
        spår.ändelse("t")
        return bas + "tt"                          # nytt
    spår.ändelse("t")
    return bas + "t"


def _adjplural(bas: str, spår: Spår) -> str:
    if _obetonat_slut(bas) and spår("obetonat_e_faller"):
        spår.ändelse("a")
        return _före_konsonant(bas[:-2], spår) + bas[-1] + "a"   # öppna, enkla, vackra
    if bas.endswith("ad") and _stavelser(bas) >= 2:
        spår.ändelse("ad")
        return bas + "e"                           # förvånade, men glad → glada
    if bas.endswith("sam") and spår("sam_dubblar_m"):
        spår.ändelse("a")
        return bas + "ma"                          # ensamma
    spår.ändelse("a")
    return bas + "a"


def adjektiv(info: dict, k: dict, spår: Spår) -> dict:
    bas = info["bas"]
    oböjligt = bas.endswith(("a", "e"))            # bra, lila, rosa, orange, levande
    ut: dict[str, str | None] = {}

    spår.cell = "obest_f_sg_pos"
    if oböjligt:
        ut["obest_f_sg_pos"] = bas
        spår.ändelse("oböjligt")
    else:
        ut["obest_f_sg_pos"] = _neutrum(bas, spår)
    spår.cell = "obest_a_pl_pos"
    svaga = ("obest_a_pl_pos", "best_a_sg_pos", "best_a_pl_pos")
    if "obest_a_pl_pos" in k:
        pl = k["obest_a_pl_pos"]
        spår.ändelse("som_plural", *svaga[1:])
    elif oböjligt:
        pl = bas
        spår.ändelse("oböjligt", *svaga)
    else:
        pl = _adjplural(bas, spår)
        spår.ändelse(spår.klasser["obest_a_pl_pos"], *svaga[1:])
    ut.update({"obest_a_pl_pos": pl, "best_a_sg_pos": pl, "best_a_pl_pos": pl})

    spår.cell = "komp"
    if "komp" in k:
        komp = k["komp"]
    elif oböjligt or (bas.endswith("ad") and _stavelser(bas) >= 2):
        komp = None                                # mer förvånad — participen kompareras med mer
    else:
        komp = (pl[:-1] if pl.endswith("a") else pl) + "are"
        spår.ändelse("are")
    ut["komp"] = komp

    spår.cell = "obest_superl"
    if "obest_superl" in k:
        superl = k["obest_superl"]
    elif komp and komp.endswith("are"):
        superl = komp[:-3] + "ast"                 # billigast
        spår.ändelse("are")
    elif komp and komp.endswith("re"):
        superl = komp[:-2] + "st"                  # större → störst
        spår.ändelse("re")
    else:
        superl = None
    ut["obest_superl"] = superl
    spår.cell = "best_superl"
    ut["best_superl"] = None if superl is None else superl + ("e" if superl.endswith("ast") else "a")
    if superl is not None:
        spår.ändelse("ast" if superl.endswith("ast") else "st")
    ut.update(k)
    return ut


def _adjdatafel(facit: dict, info: dict) -> dict:
    """Två samband utan undantag: en syntetisk komparativ är aldrig lika med
    grundformen, och en komparativ på -are bygger på pluralens stam."""
    ut = {}
    bas, pl, komp = facit.get("obest_m_sg_pos"), facit.get("obest_a_pl_pos"), facit.get("komp")
    if komp and komp == bas:
        for c in ("komp", "obest_superl", "best_superl"):
            if facit.get(c) == bas:
                ut[c] = "gradform lika med grundformen"
    elif komp and pl and komp.endswith("are") and pl.endswith("a") and komp[:-3] != pl[:-1]:
        skäl = f"plural och komparativ har olika stam ({pl} / {komp})"
        for c in ("komp", "obest_superl", "best_superl"):
            if facit.get(c):
                ut[c] = skäl
    return ut


# ── samlat ───────────────────────────────────────────────────────────────

ORDKLASSER = {
    "Verb": Ordklass(VERBORDNING, _verbbas, verb, _verbdatafel),
    "Substantiv": Ordklass(SUBSTORDNING, _substbas, substantiv, _substdatafel),
    "Adjektiv": Ordklass(ADJORDNING, _adjbas, adjektiv, _adjdatafel, saknad=("komp",)),
}

CELLNAMN = {
    "pres": "presens", "pret": "preteritum", "sup": "supinum", "imp": "imperativ",
    "perfpart_obest_utr_sg": "particip utr", "perfpart_obest_neu_sg": "particip neutr",
    "perfpart_a": "particip pl", "inf_passiv": "inf. passiv",
    "pres_passiv": "pres. passiv", "pret_passiv": "pret. passiv", "sup_passiv": "sup. passiv",
    "best_sg_ack_dat_nom": "best. sg", "obest_pl_ack_dat_nom": "plural",
    "best_pl_ack_dat_nom": "best. pl", "obest_sg_gen": "gen. sg", "best_sg_gen": "gen. best. sg",
    "obest_pl_gen": "gen. pl", "best_pl_gen": "gen. best. pl",
    "obest_f_sg_pos": "neutrum", "obest_a_pl_pos": "plural", "best_a_sg_pos": "best. sg",
    "best_a_pl_pos": "best. pl", "komp": "komparativ", "obest_superl": "superlativ",
    "best_superl": "best. superlativ",
}

# Avgjort 2026-09-13 (Julius): utrala substantiv på konsonant (`bil → bilar`,
# `park → parker`), dubbelteckning efter kort vokal (`man → mannen`), starka
# verbs supinum (`skrivit`, `sprungit`) och betonad slutstavelse (`gammal →
# gamla`, `normal → normala`) syns inte i stavningen eller gäller en sluten
# grupp, och blir därför kort per ord (KÄRNAN 3.4). Reglerna gör redan så.
GRANSKA = (
    "**Komparation.** Datan har syntetisk komparativ för ord där svenskan hellre "
    "säger mer (`intressantare`, `normalare`). Reglerna förutsäger dem, så de syns "
    "inte som kort här — men de avgör om renderaren skriver `intressantare` eller "
    "`mer intressant`.",
)
