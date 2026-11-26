#!/usr/bin/env python3
"""
bygg_ordbok.py — Bygg ordbok från CEFR-Annotated WordNet

Strategi:
  1. Utgå från CEFR-Annotated WN (6 290 engelska lemma+pos med A1–C2)
  2. Varje (lemma, pos) = ett Koncept med ett synset-ID (ILI)
  3. Varje Koncept får max ett Lexem per språk (det kanoniska lemmat)
  4. Engelska: exakt 6 290 lexem
  5. Övriga språk: färre, beroende på WordNet-täckning

Output:
  ordbok/ordbok.db                    — ren databas
  ordbok/saknade_översättningar.json  — ord utan översättning per språk

Kör:
  python3 bygg_ordbok.py
"""

import json, os, sqlite3, warnings
from collections import defaultdict
from typing import Optional

warnings.filterwarnings('ignore')
import wn

BASE    = os.path.expanduser('~/Projects/Språkprogrammet')
CEFR_WN = os.path.join(BASE, 'ordbok/cefrlex/data/wordnet_sensekey_cefr.tsv')
DB_PATH = os.path.join(BASE, 'ordbok/ordbok.db')
SAKNADE = os.path.join(BASE, 'ordbok/saknade_översättningar.json')

ANDRA_LEXIKON = {
    'de': 'odenet:1.4',
    'fr': 'omw-fr:1.4',
    'es': 'omw-es:1.4',
    'sv': 'omw-sv:1.4',
    'it': 'omw-it:1.4',
    'ja': 'omw-ja:1.4',
}

SPRÅK    = ['en', 'de', 'fr', 'es', 'sv', 'it', 'ja']
NIVÅ_ORD = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
POS_KOD  = {'1': 'n', '2': 'v', '3': 'a', '4': 'r', '5': 'a'}
POS_NAMN = {'n': 'Substantiv', 'v': 'Verb', 'a': 'Adjektiv', 'r': 'Adverb'}

SCHEMA = """
CREATE TABLE IF NOT EXISTS Koncept (
    id        INTEGER PRIMARY KEY,
    lemma_en  TEXT    NOT NULL,
    ordklass  TEXT    NOT NULL,
    nivå      TEXT    NOT NULL,
    ili       TEXT    UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_koncept_nivå ON Koncept(nivå);

CREATE TABLE IF NOT EXISTS Lexem (
    id         INTEGER PRIMARY KEY,
    koncept_id INTEGER NOT NULL REFERENCES Koncept(id) ON DELETE CASCADE,
    språk      TEXT    NOT NULL,
    lemma      TEXT    NOT NULL,
    UNIQUE(koncept_id, språk)
);
CREATE INDEX IF NOT EXISTS idx_lexem_spraak ON Lexem(språk);
CREATE INDEX IF NOT EXISTS idx_lexem_lemma  ON Lexem(lemma);
"""


def lägsta_nivå(a: Optional[str], b: Optional[str]) -> Optional[str]:
    if a is None: return b
    if b is None: return a
    return a if NIVÅ_ORD.get(a, 99) <= NIVÅ_ORD.get(b, 99) else b


def ladda_cefr(path: str) -> dict:
    """→ {(lemma, wn_pos): nivå}  (lägsta nivå per lemma+pos)"""
    res = {}
    with open(path) as f:
        for rad in f:
            rad = rad.strip()
            if not rad or '\t' not in rad:
                continue
            sk, nivå = rad.split('\t', 1)
            if '%' not in sk:
                continue
            lemma, rest = sk.split('%', 1)
            pos = POS_KOD.get(rest.split(':')[0])
            if not pos:
                continue
            key = (lemma.lower().replace('_', ' '), pos)
            res[key] = lägsta_nivå(res.get(key), nivå.strip())
    return res


def bygg_ili_till_lemma() -> dict:
    """
    Förindexera alla icke-engelska lexikon.
    → {ili_id: {språk: kanoniskt_lemma}}
    Kanoniskt = kortaste lemmat (undviker sammansättningar och fraser).
    """
    index = defaultdict(dict)
    for språk, lexikon in ANDRA_LEXIKON.items():
        antal = 0
        for synset in wn.synsets(lexicon=lexikon):
            ili = synset.ili
            if not ili:
                continue
            ili_id = ili.id
            lemman = [s.word().lemma() for s in synset.senses()]
            if lemman and ili_id not in index or språk not in index.get(ili_id, {}):
                # Välj kortaste lemmat som kanoniskt
                index[ili_id][språk] = min(lemman, key=len)
                antal += 1
        print(f'   {språk.upper()}: {antal:>6} synsets indexerade')
    return dict(index)


def main():
    # ── 1. Ladda CEFR-listan ─────────────────────────────────────────────────
    print('\n1. Laddar CEFR-Annotated WordNet...')
    cefr = ladda_cefr(CEFR_WN)
    print(f'   {len(cefr)} unika (lemma, pos)-kombinationer')
    for n in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        c = sum(1 for v in cefr.values() if v == n)
        print(f'   {n}: {c}')

    # ── 2. Förindexera andra språk ───────────────────────────────────────────
    print('\n2. Förindexerar icke-engelska WordNet-lexikon...')
    ili_till_lemma = bygg_ili_till_lemma()
    print(f'   {len(ili_till_lemma)} ILI med minst en översättning')

    # ── 3. Slå upp engelska synsets och hämta ILI ────────────────────────────
    print('\n3. Matchar CEFR-ord mot engelska synsets...')

    koncept_data = []
    saknade      = defaultdict(list)
    ej_i_wn      = []

    sorterade = sorted(cefr.items(), key=lambda x: (NIVÅ_ORD.get(x[1], 99), x[0]))

    for (lemma, pos), nivå in sorterade:
        # Hitta engelska synsets — prova ewn:2020 först, sedan omw-en
        en_synsets = wn.synsets(lemma, pos=pos, lexicon='ewn:2020')
        if not en_synsets:
            en_synsets = wn.synsets(lemma, pos=pos, lexicon='omw-en:1.4')

        # Välj det synset som har flest ILI-kopplingar till andra språk
        bästa_ili  = None
        bästa_täckning = -1
        for s in en_synsets:
            if not s.ili:
                continue
            täckning = len(ili_till_lemma.get(s.ili.id, {}))
            if täckning > bästa_täckning:
                bästa_täckning = täckning
                bästa_ili = s.ili.id

        if bästa_ili is None and en_synsets:
            # Ta första synset utan ILI — sällsynt
            bästa_ili = None

        if not en_synsets:
            ej_i_wn.append({'lemma': lemma, 'pos': POS_NAMN.get(pos, pos), 'nivå': nivå})

        # Bygg lexem per språk
        lexem = {'en': lemma}  # Engelska = CEFR-ordet självt
        if bästa_ili:
            for sp, kanon in ili_till_lemma.get(bästa_ili, {}).items():
                lexem[sp] = kanon

        # Spåra saknade
        for sp in ['de', 'fr', 'es', 'sv', 'it', 'ja']:
            if sp not in lexem:
                saknade[sp].append({
                    'lemma': lemma,
                    'pos':   POS_NAMN.get(pos, pos),
                    'nivå':  nivå,
                })

        koncept_data.append({
            'lemma': lemma,
            'pos':   pos,
            'nivå':  nivå,
            'ili':   bästa_ili,
            'lexem': lexem,
        })

    print(f'   {len(koncept_data)} koncept matchade')
    print(f'   {len(ej_i_wn)} ord ej hittade i WordNet alls')

    # ── 4. Skapa databas ─────────────────────────────────────────────────────
    print(f'\n4. Skapar databas: {DB_PATH}')
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA foreign_keys = ON')
    con.execute('PRAGMA journal_mode = WAL')
    con.executescript(SCHEMA)
    con.commit()

    dubbletter = 0
    for kd in koncept_data:
        try:
            cur = con.execute(
                'INSERT INTO Koncept (lemma_en, ordklass, nivå, ili) VALUES (?, ?, ?, ?)',
                (kd['lemma'], POS_NAMN.get(kd['pos'], kd['pos']), kd['nivå'], kd['ili'])
            )
            kid = cur.lastrowid
        except sqlite3.IntegrityError:
            # Samma ILI finns redan — behåll den med lägst CEFR-nivå
            dubbletter += 1
            if kd['ili']:
                existing = con.execute(
                    'SELECT id, nivå FROM Koncept WHERE ili = ?', (kd['ili'],)
                ).fetchone()
                if existing and NIVÅ_ORD.get(kd['nivå'], 99) < NIVÅ_ORD.get(existing[1], 99):
                    con.execute(
                        'UPDATE Koncept SET lemma_en = ?, nivå = ? WHERE id = ?',
                        (kd['lemma'], kd['nivå'], existing[0])
                    )
            continue

        for sp, lemma in kd['lexem'].items():
            try:
                con.execute(
                    'INSERT INTO Lexem (koncept_id, språk, lemma) VALUES (?, ?, ?)',
                    (kid, sp, lemma)
                )
            except sqlite3.IntegrityError:
                pass

    if dubbletter:
        print(f'   {dubbletter} ILI-kollisioner hanterade (synonymer i CEFR-listan)')

    con.commit()

    # ── 5. Statistik ─────────────────────────────────────────────────────────
    k_tot = con.execute('SELECT COUNT(*) FROM Koncept').fetchone()[0]
    l_tot = con.execute('SELECT COUNT(*) FROM Lexem').fetchone()[0]

    print(f'\n5. Resultat:')
    print(f'   Koncept: {k_tot}')
    print(f'   Lexem:   {l_tot}  (max möjligt: {k_tot * len(SPRÅK)})')

    print(f'\n   Täckning per språk:')
    for sp in SPRÅK:
        n   = con.execute('SELECT COUNT(*) FROM Lexem WHERE språk = ?', (sp,)).fetchone()[0]
        pct = 100 * n / k_tot
        print(f'   {sp.upper()}: {n:>5} / {k_tot} ({pct:5.1f}%)  — {k_tot - n} saknas')

    print(f'\n   Täckning per nivå och språk:')
    print(f'   {"":6}', end='')
    for sp in SPRÅK:
        print(f'{sp.upper():>8}', end='')
    print()

    for nivå in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        tot = con.execute('SELECT COUNT(*) FROM Koncept WHERE nivå = ?', (nivå,)).fetchone()[0]
        print(f'   {nivå:6}', end='')
        for sp in SPRÅK:
            n   = con.execute('''
                SELECT COUNT(*) FROM Lexem l
                JOIN Koncept k ON k.id = l.koncept_id
                WHERE l.språk = ? AND k.nivå = ?
            ''', (sp, nivå)).fetchone()[0]
            pct = 100 * n / tot if tot else 0
            print(f'{pct:7.0f}%', end='')
        print(f'   ({tot})')

    con.close()

    # ── 6. Spara saknade ─────────────────────────────────────────────────────
    print(f'\n6. Sparar saknade → {SAKNADE}')
    with open(SAKNADE, 'w', encoding='utf-8') as f:
        json.dump(dict(saknade), f, ensure_ascii=False, indent=2)
    for sp in ['de', 'fr', 'es', 'sv', 'it', 'ja']:
        print(f'   {sp.upper()}: {len(saknade[sp])} saknas')

    print('\n✅ Klart!')


if __name__ == '__main__':
    main()
