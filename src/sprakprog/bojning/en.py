"""Engelska böjningsregler — steg 0, KÄRNAN 3.4.

Samma uppbyggnad som `sv.py`. Reglerna är skrivna ur standardgrammatik och inte
härledda ur datan, så att de kan prövas MOT datan. Datan är amerikansk engelska
(`traveled`, `practiced`, `gotten`).

KORTEN, OCH VAR DE SYNS HÄR

  ändelse       -s, -ed, -ing; plural -s; komparativ -er, superlativ -est
  regel         stavningsanpassningar, loggade med namn i `Spår` (LJUDREGLER)
  oregelbunden  det förutsägelsen missar — hittas av kontrollen, inte här

SUPINUM FÖRUTSÄGS VARA PRETERITUM. Så är det i alla regelbundna verb och i många
oregelbundna (`bought`, `made`). Ett starkt verb får därför både preteritum och
supinum som kort (`wrote`, `written`), ett svagt oregelbundet bara preteritum.

PERSONFORMERNA ÄR LIKA. Utom tredje person singular presens har ett engelskt verb
samma form i alla personer. Bara `be` avviker, och varje personform förutsägs ur
den föregående: `am` blir kort, `are` blir kort, och resten av pluralen följer.

KOMPARATIONEN FÖLJER STAVELSERNA. Enstaviga adjektiv och tvåstaviga på -y
kompareras med -er och -est, övriga med `more` och `most` — och har då ingen
komparativ i datan. Ett ord som avviker åt ena hållet får kort (`narrower`); åt
andra hållet står det bland formerna reglerna ger men datan saknar.

SLUTNA GRUPPER ÄR KORT PER ORD (KÄRNAN 3.4). Plural på -oes (`potatoes`) och -ves
(`lives`) gäller slutna grupper — nya ord får `photos`, `roofs` — och verben på -o
(`does`, `goes`) är två. Dubbeltecknad konsonant i flerstaviga ord (`forgetting`
men `visiting`) beror på betoningen, som inte syns i stavningen.

Där ett val är tveksamt står det i GRANSKA längst ner.
"""

from __future__ import annotations

from . import Ordklass, Spår

NAMN = "engelska"

VOKAL = frozenset("aeiou")
SIBILANT = ("s", "x", "z", "ch", "sh")


# ── stavningsregler ──────────────────────────────────────────────────────

LJUDREGLER = {
    "sibilant_tar_es": "efter s, x, z, ch och sh blir -s -es: misses, beaches, buses",
    "konsonant_y_blir_i": "y efter konsonant blir i före -s, -ed, -er och -est: carries, cried, cities, happier",
    "e_smälter_med_e": "ett slut-e smälter ihop med en ändelse på e: liked, agreed, braver, freest",
    "stumt_e_faller": "stumt slut-e faller före -ing: making, using — men seeing, being",
    "ie_blir_y": "ie blir y före -ing: dying, lying",
    "enstavig_dubblar": "enstavigt ord på vokal + konsonant dubbeltecknar före en vokal: stopped, running, bigger",
}


def _vokalgrupper(ord: str) -> int:
    """Vokalgrupper; y räknas som vokal efter en konsonant (happy, dry)."""
    antal, föregående = 0, False
    for i, tecken in enumerate(ord):
        vokal = tecken in VOKAL or (tecken == "y" and i > 0 and ord[i - 1] not in VOKAL)
        antal += vokal and not föregående
        föregående = vokal
    return antal


def _stavelser(ord: str) -> int:
    """Stavelser ur stavningen: vokalgrupperna, utom ett stumt slut-e (brave,
    whole). Slut-le efter konsonant är en egen stavelse (purple)."""
    antal = _vokalgrupper(ord)
    stumt_e = (len(ord) > 2 and ord.endswith("e") and ord[-2] not in VOKAL
               and not (ord.endswith("le") and ord[-3] not in VOKAL))
    return antal - 1 if stumt_e and antal > 1 else antal


def _konsonant_y(stam: str) -> bool:
    return len(stam) >= 2 and stam[-1] == "y" and stam[-2] not in VOKAL


def _dubblar(stam: str) -> bool:
    """Enstavigt ord på en ensam vokal och en konsonant: stop, big, run — inte
    fix, new, cook."""
    return (len(stam) >= 3 and _vokalgrupper(stam) == 1 and stam[-1] not in VOKAL
            and stam[-1] not in "wxy" and stam[-2] in VOKAL and stam[-3] not in VOKAL)


def _ändelse(stam: str, ändelse: str, spår: Spår) -> str:
    """Stam plus -s, -ed, -ing, -er eller -est, med stavningsreglerna."""
    if ändelse == "s":
        if stam.endswith(SIBILANT):
            spår("sibilant_tar_es")
            return stam + "es"
        if _konsonant_y(stam):
            spår("konsonant_y_blir_i")
            return stam[:-1] + "ies"
        return stam + "s"
    if ändelse == "ing":
        if stam.endswith("ie"):
            spår("ie_blir_y")
            return stam[:-2] + "ying"
        if (stam.endswith("e") and not stam.endswith(("ee", "oe", "ye"))
                and any(t in VOKAL for t in stam[:-1])):
            spår("stumt_e_faller")
            return stam[:-1] + "ing"
        if _dubblar(stam):
            spår("enstavig_dubblar")
            return stam + stam[-1] + "ing"
        return stam + "ing"
    if stam.endswith("e"):                        # -ed, -er, -est
        spår("e_smälter_med_e")
        return stam + ändelse[1:]
    if _konsonant_y(stam):
        spår("konsonant_y_blir_i")
        return stam[:-1] + "i" + ändelse
    if _dubblar(stam):
        spår("enstavig_dubblar")
        return stam + stam[-1] + ändelse
    return stam + ändelse


# ── verb ─────────────────────────────────────────────────────────────────

VERBORDNING = ("pres_3sg", "pret", "sup", "gerund",
               "pres_1sg", "pres_2sg", "pres_1pl", "pres_2pl", "pres_3pl",
               "pret_2sg", "pret_1pl", "pret_2pl", "pret_3pl")


def _verbbas(facit: dict, lexem) -> tuple[dict, dict]:
    """Grundformen är infinitiven. Partikel och objekt i lemmat följer med varje
    form ("wakes up", "gets married") och skalas av. Modalverben saknar
    infinitiv; där är lemmat grundformen."""
    huvud, _, rest = lexem["lemma"].partition(" ")
    svans = " " + rest if rest else ""
    norm = {}
    for cell, form in facit.items():
        if form:
            norm[cell] = form[:-len(svans)] if svans and form.endswith(svans) else form
    return {"bas": norm.get("inf_imp") or huvud}, norm


def verb(info: dict, k: dict, spår: Spår) -> dict:
    bas = info["bas"]
    ut: dict[str, str | None] = {}

    spår.cell = "pres_3sg"
    ut["pres_3sg"] = k["pres_3sg"] if "pres_3sg" in k else _ändelse(bas, "s", spår)

    spår.cell = "pret"
    pret = k["pret"] if "pret" in k else _ändelse(bas, "ed", spår)
    ut["pret"] = pret

    spår.cell = "sup"
    ut["sup"] = k.get("sup", pret)

    spår.cell = "gerund"
    if "gerund" in k:
        ut["gerund"] = k["gerund"]
    elif pret == bas + bas[-1] + "ed" and not _dubblar(bas):
        ut["gerund"] = bas + bas[-1] + "ing"       # preferred → preferring
    else:
        ut["gerund"] = _ändelse(bas, "ing", spår)

    ut["pres_1sg"] = k.get("pres_1sg", bas)
    ut["pres_2sg"] = k.get("pres_2sg", ut["pres_1sg"])
    for cell in ("pres_1pl", "pres_2pl", "pres_3pl"):
        ut[cell] = k.get(cell, ut["pres_2sg"])
    ut["pret_2sg"] = k.get("pret_2sg", pret)
    for cell in ("pret_1pl", "pret_2pl", "pret_3pl"):
        ut[cell] = k.get(cell, ut["pret_2sg"])
    ut.update(k)
    return ut


def _verbdatafel(facit: dict, info: dict) -> dict:
    """Verben har inget samband utan undantag: även -s i tredje person saknas
    i modalverben."""
    return {}


# ── substantiv ───────────────────────────────────────────────────────────

SUBSTORDNING = ("pl", "sg_gen", "pl_gen")


def _plgenitiv(pl: str) -> str:
    return pl + "'" if pl.endswith("s") else pl + "'s"


def _substbas(facit: dict, lexem) -> tuple[dict, dict]:
    norm = {c: f for c, f in facit.items() if f}
    sg = norm.get("sg")
    return {"bas": sg or norm.get("pl") or lexem["lemma"], "tantum": not sg}, norm


def substantiv(info: dict, k: dict, spår: Spår) -> dict:
    bas, tantum = info["bas"], info["tantum"]
    spår.cell = "pl"
    if "pl" in k:
        pl = k["pl"]
    else:
        pl = bas if tantum else _ändelse(bas, "s", spår)
    ut = {"pl": pl, "sg_gen": None if tantum else bas + "'s", "pl_gen": _plgenitiv(pl)}
    ut.update(k)
    return ut


def _substdatafel(facit: dict, info: dict) -> dict:
    """Två samband utan undantag: genitiv singular är formen plus 's, och
    genitiv plural är pluralen plus ' efter -s och plus 's annars (children's)."""
    ut = {}
    sg, pl = facit.get("sg"), facit.get("pl")
    if facit.get("sg_gen") and sg and facit["sg_gen"] != sg + "'s":
        ut["sg_gen"] = f"genitiv ≠ form + 's ({sg} → {sg}'s)"
    if facit.get("pl_gen") and pl and facit["pl_gen"] != _plgenitiv(pl):
        ut["pl_gen"] = f"genitiv ≠ plural + ' eller 's ({pl} → {_plgenitiv(pl)})"
    return ut


# ── adjektiv ─────────────────────────────────────────────────────────────

ADJORDNING = ("komp", "superl")


def _adjbas(facit: dict, lexem) -> tuple[dict, dict]:
    norm = {c: f for c, f in facit.items() if f}
    return {"bas": norm.get("pos") or lexem["lemma"]}, norm


def adjektiv(info: dict, k: dict, spår: Spår) -> dict:
    bas = info["bas"]
    stavelser = _stavelser(bas)

    spår.cell = "komp"
    if "komp" in k:
        komp = k["komp"]
    elif " " not in bas and (stavelser == 1 or (stavelser == 2 and bas.endswith("y"))):
        komp = _ändelse(bas, "er", spår)
    else:
        komp = None                                # more interesting, more in love

    spår.cell = "superl"
    if "superl" in k:
        superl = k["superl"]
    elif komp and komp.endswith("er"):
        superl = komp[:-2] + "est"                 # bigger → biggest
    else:
        superl = None
    ut = {"komp": komp, "superl": superl}
    ut.update(k)
    return ut


def _adjdatafel(facit: dict, info: dict) -> dict:
    """Inget samband utan undantag: better → best bryter mönstret -er → -est."""
    return {}


# ── samlat ───────────────────────────────────────────────────────────────

ORDKLASSER = {
    "Verb": Ordklass(VERBORDNING, _verbbas, verb, _verbdatafel),
    "Substantiv": Ordklass(SUBSTORDNING, _substbas, substantiv, _substdatafel),
    "Adjektiv": Ordklass(ADJORDNING, _adjbas, adjektiv, _adjdatafel, saknad=("komp",)),
}

CELLNAMN = {
    "pres_3sg": "presens 3 sg", "pret": "preteritum", "sup": "particip",
    "gerund": "ing-form", "pres_1sg": "presens 1 sg", "pres_2sg": "presens 2 sg",
    "pres_1pl": "presens 1 pl", "pres_2pl": "presens 2 pl", "pres_3pl": "presens 3 pl",
    "pret_2sg": "preteritum 2 sg", "pret_1pl": "preteritum 1 pl",
    "pret_2pl": "preteritum 2 pl", "pret_3pl": "preteritum 3 pl",
    "pl": "plural", "sg_gen": "genitiv sg", "pl_gen": "genitiv pl",
    "komp": "komparativ", "superl": "superlativ",
}

GRANSKA = (
    "**Amerikansk engelska.** Datan stavar och böjer amerikanskt: `traveled`, "
    "`practiced`, `gotten`, `learned`, `gray`, `neighbor`. Brittiska former "
    "(`travelled`, `got`, `learnt`, `grey`) räknas i dag som fel. Ska de godtas "
    "som varianter (KÄRNAN 8.3)?",
    "**Komparation.** För `half`, `whole` och `wrong` ger reglerna en form på -er "
    "som datan saknar; orden går knappast att komparera alls. `purpler` och "
    "`yellower` står i datan men är ovanliga mot `more purple`, och `deader`, "
    "`readier` och `pinker` följer reglerna men är ovanliga.",
)
