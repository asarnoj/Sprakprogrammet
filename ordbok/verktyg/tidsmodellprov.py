"""Nät för tidsmodellen — KÄRNAN 5.5.

VARFÖR DET HÄR NÄTET FINNS. Modellen svarar med ett tal som styr hur mycket nytt
en dag får innehålla, och ett fel i den riktningen märks inte: en användare som
får för mycket nytt tror att kursen är svår, inte att modellen räknar fel. Två
fel fanns i första bygget, och båda var tysta.

    HORISONTEN     5.5 säger «över dagarna t fram till kursens slut», och det
                   räcker inte. Ett kort kostar arbete i över ett år, så
                   arbetsbördans topp ligger EFTER sista införandet. Räknat bara
                   till slutdagen blir det en skenande återkoppling: stort n ger
                   kort kurs, kort kurs räknar bara de första dagarnas arbete,
                   billiga kort ger större n. En timme om dagen gav 265 nya kort
                   dagligen och en kurs på sex dagar.

    INTRODUKTIONEN Att införa ett kort kostade en repetition i modellen. Men
                   introfasen bokför ingenting (5.4) och tar ändå tid, och 5.5
                   räknar den: «tid per introövning, med omtag». Utan den blev
                   dagens första kort nästan gratis.

Båda felen pekar samma väg — FÖR MÅNGA nya kort — och 5.5 säger uttryckligen att
osäkerhet ska falla åt andra hållet: «det ger färre nya kort, aldrig fler».

Kör:  python ordbok/verktyg/tidsmodellprov.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.passet.tid import (                                # noqa: E402
    Meningstid, Tidsmodell, arbetsprofil,
)

MENINGSTID = ROT / "ordbok" / "nivålistor" / "meningstid.csv"

#: Profilen måste täcka kortets hela svans. Ett år plus marginal.
DAGAR = 400


def _modell(profil, mt: Meningstid, täthet: float | None = None) -> Tidsmodell:
    return Tidsmodell(profil, mt, täthet or mt.täthet,
                      mt.fast + mt.per_kort)


def profilen_stämmer_med_den_gamla_mätningen(profil, mt) -> list[str]:
    """Väntevärdet ska ge samma tal som den gamla modulens Monte Carlo.

    `kort/arbetsborda.py` mätte 3,7 repetitioner den första månaden och 8,4 det
    första året genom att dra slumptal. Den här profilen räknar i stället
    sannolikheterna dag för dag. De två ska mötas — annars är minst en av dem
    fel, och då vet vi inte vilken.
    """
    månad, år = sum(profil[:31]), sum(profil)
    brister = []
    if not 3.5 <= månad <= 3.9:
        brister.append(f"första månaden gav {månad:.2f} repetitioner, "
                       "den gamla mätningen 3,7")
    if not 8.0 <= år <= 8.8:
        brister.append(f"första året gav {år:.2f} repetitioner, "
                       "den gamla mätningen 8,4")
    return brister


def upplösningen_har_konvergerat(profil, mt) -> list[str]:
    """Rutnätet som slår ihop tillstånden ska vara fint nog att inte märkas.

    Talet är mätt fram, inte valt: en dubblering av upplösningen får inte flytta
    årssumman mer än en promille. Gör den det är `UPPLÖSNING` för grov, och
    modellen underskattar arbetet — vilket släpper in fler nya kort.
    """
    from sprakprog.passet.tid import UPPLÖSNING
    grov, _ = arbetsprofil(0.9, DAGAR, upplösning=UPPLÖSNING)
    fin, _ = arbetsprofil(0.9, DAGAR, upplösning=UPPLÖSNING * 2)
    skillnad = abs(sum(fin) - sum(grov)) / sum(fin)
    return ([f"en dubblerad upplösning flyttar årssumman {100*skillnad:.2f} %, "
             "alltså är rutnätet för grovt"] if skillnad > 0.001 else [])


def ingen_dag_spränger_budgeten(profil, mt, intro=None) -> list[str]:
    """Tempot modellen ger ska hålla VARJE dag, inte bara till kursens slut.

    Det är hela påståendet i 5.5 — «det största jämna tempo som ryms varje dag»
    — och det enda som går att pröva utifrån. Provet tar n ur modellen, räknar
    arbetet dag för dag ett år efter sista införandet, och kräver att ingen dag
    går över T.

    ATT MÄTA DET HÄR OCH INTE «n VÄXER LINJÄRT MED TIDEN» var en rättelse av
    provet. Tempot växer FASTARE än tiden, och det är riktigt: den bindande dagen
    är sista införandedagen, och en kortare kurs hinner bara samla en del av
    kortets livstidskostnad innan dess — resten sprids över året efteråt och
    ryms. Vid tjugo minuter har 56 % av kostnaden fallit ut på slutdagen, vid
    sextio bara 41 %. Ett prov som kräver linjäritet fäller alltså en korrekt
    modell.

    `intro` finns för falsifieringen: med en gratis introduktion skenar tempot,
    och då ska det här provet fälla.
    """
    m = (_modell(profil, mt) if intro is None
         else Tidsmodell(profil, mt, mt.täthet, intro))
    brister = []
    for minuter in (10, 20, 60):
        T = minuter * 60
        r = m.tempo(minuter, [], 951)
        if not r.nya or r.slutdagen is None:
            continue
        värst, värsta_dagen = 0.0, 0
        for t in range(r.slutdagen + len(profil)):
            # Arbetet dag t: varje kort som införts dag 0..min(t, slutdagen)
            # är nu i profilens läge t − dagen.
            arbete = 0.0
            for dag in range(min(t, r.slutdagen) + 1):
                ålder = t - dag
                if ålder < len(profil):
                    arbete += r.nya * profil[ålder] * m.per_repetition
                if ålder == 0:
                    arbete += r.nya * m.introsekunder
            if arbete > värst:
                värst, värsta_dagen = arbete, t
        # En kortavrundning nedåt ger alltid lite luft; en procents överdrag är
        # avrundning, tio procent är ett fel.
        if värst > T * 1.01:
            brister.append(
                f"{minuter} min gav {r.nya} kort/dag, men dag {värsta_dagen} "
                f"kräver {värst/60:.1f} min")
    return brister


def mer_arbete_ger_färre_kort(profil, mt) -> list[str]:
    """En tyngre kortlek ska sänka tempot, monotont.

    Riktningen är hela poängen med 5.5: «har arbetsbördan vuxit, till exempel
    efter några missade dagar, blir n noll».
    """
    m = _modell(profil, mt)
    förra = None
    brister = []
    for antal in (0, 100, 400, 1000, 3000):
        åldrar = [i % 60 for i in range(antal)]
        n = m.tempo(20, åldrar, 951).nya
        if förra is not None and n > förra:
            brister.append(f"{antal} införda kort gav {n} nya, "
                           f"färre kort gav {förra}")
        förra = n
    if förra:
        brister.append(f"3000 införda kort gav fortfarande {förra} nya per dag — "
                       "arbetsbördan biter inte")
    return brister


def introduktionen_kostar(profil, mt) -> list[str]:
    """Att införa ett kort ska kosta mer än att repetera det.

    Introfasen bokför ingenting (5.4) men tar tid, och 5.5 räknar den. Var den
    gratis blev dagens första kort nästan fritt.
    """
    utan = Tidsmodell(profil, mt, mt.täthet, 0.0).tempo(20, [], 951).nya
    med = _modell(profil, mt).tempo(20, [], 951).nya
    return ([f"introduktionen kostade ingenting: {med} nya kort med den, "
             f"{utan} utan — den räknas inte"] if med >= utan else [])


def utan_mått_inget_svar(profil, mt) -> list[str]:
    """Saknas mätningen svarar modellen inte alls, i stället för att gissa.

    «Utan det talet finns ingen väg från minuter till kort» — samma regel som
    `sekunder_per_repetition` i det gamla systemet följer.
    """
    saknas = Meningstid.ur_fil(ROT / "finns-inte.csv")
    return ([] if saknas is None else
            ["en fil som inte finns gav ändå en meningstid"])


PROV = [
    ("profilen stämmer med den gamla mätningen", profilen_stämmer_med_den_gamla_mätningen),
    ("upplösningen har konvergerat", upplösningen_har_konvergerat),
    ("ingen dag spränger budgeten", ingen_dag_spränger_budgeten),
    ("mer arbete ger färre kort", mer_arbete_ger_färre_kort),
    ("introduktionen kostar", introduktionen_kostar),
    ("utan mått inget svar", utan_mått_inget_svar),
]


def _falsifiera(profil, mt) -> list[str]:
    """Varje gammalt läge ska fälla sitt prov.

    TVÅ GISSNINGAR STOD HÄR FÖRST, och båda var fel. Att de föll är värt att
    skriva ner, för de visar vad provet FAKTISKT vaktar.

    Den korta horisonten — att minimera bara till kursens slut, som 5.5 står
    skriven — ger 30 kort vid tjugo minuter mot 27 med hela horisonten. Dagarna
    efter sista införandet binder aldrig, för då är arbetet utspritt över året.
    Skillnaden syns inte, så horisonten bär inte talet. Det gör
    INTRODUKTIONSKOSTNADEN: utan den gav en timme om dagen 265 nya kort.

    Men en gratis introduktion fäller inte heller provet, och det är lärorikt:
    provet räknar arbetet med modellens EGNA kostnader. Säger modellen att
    introduktionen är gratis räknar provet likadant och finner ingen
    överdragning. Att kostnaden är rätt är en MÄTNINGSFRÅGA — den vaktas av
    `introduktionen kostar` och av `meningstidsmätning` — inte en invariant.

    Vad provet vaktar är att `n` är förenligt med bokföringen: att minimeringen
    verkligen tar minimum över alla dagar. Falsifieringen bryter därför just det,
    med det gamla systemets villkor «IDAG»: `prognos[0] + k × kurva[0] ≤ mål`,
    alltså bara dag noll.
    """
    import sprakprog.passet.tid as T

    def bara_idag(self, T_, åldrar, slut):
        """Det gamla systemets enda villkor för dagen: bara dag noll räknas."""
        bidrag = self._fönster(0, 0) * self.per_repetition + self.introsekunder
        if bidrag <= 0:
            return 0, 0
        return int(((T_ - self.upptaget(0, åldrar)) / bidrag) // 1), 0

    fall = [("minimeringen såg bara dag noll", "ingen dag spränger budgeten",
             T.Tidsmodell, "_minimum", bara_idag)]
    brister = []
    print("\nfalsifiering — varje gammalt läge ska fälla sitt prov:")
    for namn, invariant, klass, attr, ersättning in fall:
        gammalt = getattr(klass, attr)
        setattr(klass, attr, ersättning)
        try:
            fel = ingen_dag_spränger_budgeten(profil, mt)
        finally:
            setattr(klass, attr, gammalt)
        if fel:
            print(f"  ✓ föll  {namn}  ({fel[0][:64]}…)")
        else:
            print(f"  ✗ STUMT  {namn}")
            brister.append(f"«{invariant}» vaktar inte {namn}")
    return brister


def main() -> int:
    mt = Meningstid.ur_fil(MENINGSTID)
    if mt is None:
        print(f"ingen meningstid i {MENINGSTID} — kör "
              "ordbok/verktyg/meningstidsmätning.py först")
        return 1
    print(f"meningstid: {mt.fast:.1f} s fast + {mt.per_kort:.1f} s per kort, "
          f"täthet {mt.täthet:.0f}\n")
    profil, tillstånd = arbetsprofil(0.9, DAGAR)
    print(f"arbetsprofil: {sum(profil):.2f} repetitioner på {DAGAR} dagar, "
          f"högst {tillstånd} samtidiga tillstånd\n")

    brister: list[str] = []
    for namn, fn in PROV:
        fel = fn(profil, mt)
        print(f"  {'✓' if not fel else '✗'} {namn}")
        for b in fel:
            print(f"      {b}")
        brister += fel
    brister += _falsifiera(profil, mt)

    print(f"\n{len(PROV)} kontroller, "
          + (f"{len(brister)} brister." if brister else "alla håller."))
    return 1 if brister else 0


if __name__ == "__main__":
    raise SystemExit(main())
