#!/usr/bin/env python3
"""
tagga_egenskaper.py — Taggar grammatiska egenskaper via Ollama (qwen2.5:7b)

För Verb: två oberoende omgångar (valens, sedan personlighet)

Kör alla:
    python3 tagga_egenskaper.py

Kör bara valens (Verb):
    python3 tagga_egenskaper.py --ordklass Verb --aspekt valens

Kör bara personlighet (Verb):
    python3 tagga_egenskaper.py --ordklass Verb --aspekt personlighet

Kör Substantiv:
    python3 tagga_egenskaper.py --ordklass Substantiv

Testa utan att spara:
    python3 tagga_egenskaper.py --ordklass Verb --aspekt valens --dry-run

Justera batchstorlek (standard 25):
    python3 tagga_egenskaper.py --batch 20
"""

import sqlite3, json, requests, argparse, sys, time, math
from bitflaggor import Valens, Personlighet

OLLAMA_URL   = "http://localhost:11434/api/chat"
MODEL        = "qwen2.5:7b"
DEFAULT_DB   = "ordbok/ord.db"

# ── Konfiguration per ordklass och aspekt ────────────────────────────────────

ORDKLASSER = {

    'Verb_valens': {
        'ordklass': 'Verb',
        'kolumn':   'valens',
        'prompt_extra': """
You are classifying verbs for a multilingual language learning system.
Focus ONLY on the VALENCE (argument structure) of the verb.
Use the translations (sv/en/fr/de) to identify the exact meaning being represented.

## VALENCE — what ARGUMENTS does this verb TYPICALLY/PRIMARY use?

Work through these questions and set ALL that apply:

1. Is the verb used WITHOUT an object as its PRIMARY/MOST COMMON pattern?
   Examples: sleep (always without object), arrive, die, fall, laugh, run, jump
   Test: "[Subject] [verb]." is the MAIN/NATURAL usage (not just possible)
   → Set: INTRANSITIV

2. Does the verb's PRIMARY usage include a DIRECT OBJECT?
   Examples: eat (eat food), see (see someone), build (build a house), know (know X)
   Test: "[Subject] [verb] [something]." is how you TYPICALLY use the verb
   → Set: TRANSITIV

3. Does the verb take TWO objects (recipient + thing)?
   Test: "[Subject] [verb] [person] [thing]."
   Example: "give her a book" = give [her] [a book]
   → Set BOTH: TRANSITIV and DITRANSITIV

4. Is the verb primarily/typically reflexive (mainly used with reflexive pronoun)?
   Examples: "wash oneself", "dress oneself", "behave oneself"
   Note: can still also be TRANSITIV (e.g. "dress a child") — set both flags if so
   → Set: REFLEXIV

5. Does the verb link subject to adjective/noun (state, not action)?
   Test: "[Subject] [verb] [adjective/noun]."
   Examples: "be tired", "become angry", "seem strange"
   → Set: KOPULA (not INTRANSITIV or TRANSITIV)

## CRITICAL EXAMPLES of VALENCE patterns (DO NOT include personlighet):

  sleep        → [INTRANSITIV]              — always without object: "I sleep"
  arrive       → [INTRANSITIV]              — always without object: "he arrived"
  die          → [INTRANSITIV]              — always without object: "she died"

  eat          → [INTRANSITIV, TRANSITIV]  — both: "I eat" (intrans) AND "I eat pizza" (trans) are normal
  move         → [INTRANSITIV, TRANSITIV]  — both: "I move" (intrans, change location) AND "move a chair" (trans)
  walk         → [INTRANSITIV, TRANSITIV]  — both: "she walks" (intrans) AND "walk the dog" (trans)

  accept       → [TRANSITIV]         — primary: "accept an offer" (NOT "accept" alone)
  abandon      → [TRANSITIV]         — primary: "abandon someone" (NOT "abandon" alone)
  achieve      → [TRANSITIV]         — primary: "achieve a goal" (NOT "achieve" alone)
  know         → [TRANSITIV]         — primary: "know something" (NOT "know" alone)

  give         → [TRANSITIV, DITRANSITIV]  — takes 2 objects: "give [person] [thing]"
  tell         → [TRANSITIV, DITRANSITIV]  — takes 2 objects: "tell [person] [info]"
  send         → [TRANSITIV, DITRANSITIV]  — takes 2 objects: "send [person] [item]"

  become       → [KOPULA]            — links to state: "become angry"
  be           → [KOPULA]            — links to state/identity: "be tired", "be a doctor"

Respond ONLY with JSON:
{"resultat": [{"id": <int>, "valens": [<str>, <str>, ...]}]}

Valid valens flags: INTRANSITIV, TRANSITIV, DITRANSITIV, REFLEXIV, KOPULA
""",
    },

    'Verb_personlighet': {
        'ordklass': 'Verb',
        'kolumn':   'personlighet',
        'prompt_extra': """
You are classifying verbs for a multilingual language learning system.
Focus ONLY on the PERSONLIGHET (subject type) of the verb.
Use the translations (sv/en/fr/de) to identify the exact meaning being represented.

## PERSONLIGHET — what kind of SUBJECT can this verb take?

For each verb, answer: Can it use a REAL subject OR an IMPERSONAL dummy subject?

PERSONLIG — the verb takes a REAL, grammatical subject
  ✓ "I run", "she knows", "the wind blows", "he eats"
  → Set: PERSONLIG

OPERSONLIG — the verb uses a DUMMY/IMPERSONAL subject ("it"/"det") with no real referent
  ✓ "it rains" (det regnar)
  ✓ "it snows" (det snöar)
  ✓ "it seems" (det verkar) — when used as "it seems X"
  ✓ "it matters" (det spelar roll)
  → Set: OPERSONLIG

BOTH — the verb can be used EITHER way (most common for opersonlig verbs)
  ✓ "it rains" (opersonlig) BUT "rain falls from sky" (personlig)
  ✓ "it seems" (opersonlig) BUT "he seems tired" (personlig)
  ✓ "it rings" (det ringer) BUT "I ring him" (jag ringer honom)
  → Set: [PERSONLIG, OPERSONLIG]

## EXAMPLES (DO NOT include valens):

  sleep        → [PERSONLIG]
  move         → [PERSONLIG]
  give         → [PERSONLIG]
  become       → [PERSONLIG]
  be           → [PERSONLIG]
  rain         → [OPERSONLIG]
  snow         → [OPERSONLIG]
  seem         → [PERSONLIG, OPERSONLIG]
  ring         → [PERSONLIG, OPERSONLIG]
  matter       → [OPERSONLIG]

Respond ONLY with JSON:
{"resultat": [{"id": <int>, "personlighet": [<str>, ...]}]}

Valid personlighet flags: PERSONLIG, OPERSONLIG
""",
    },

    'Verb_rätta': {
        'ordklass':      'Verb',
        'kolumn':        'valens',
        'custom_filter': 'valens = 1',   # bara de som fått ENBART INTRANSITIV
        'rätta':         True,            # OR-uppdatering, ersätter inte befintligt värde
        'prompt_extra': """
You are reviewing verb classifications for a multilingual language learning system.
Each verb here was previously classified as INTRANSITIV (used without object).
Your job: check if the verb ALSO takes a direct object or two objects.

## QUESTION 1 — Is this verb also TRANSITIV?
Does the verb's TYPICAL/PRIMARY usage include a direct object (a noun phrase)?
  kill   → YES  ("kill someone")
  eat    → YES  ("eat food")
  follow → YES  ("follow someone")
  hide   → YES  ("hide something")
  break  → YES  ("break something")
  sleep  → NO   (never takes a direct object)
  arrive → NO   (never takes a direct object)
  pray   → NO   ("pray to someone" — preposition, NOT direct object)

## QUESTION 2 — Is this verb also DITRANSITIV?
Does the verb take TWO objects: a recipient AND a thing?
  give  → YES  ("give him a book" = give [person] [thing])
  show  → YES  ("show her the result")
  teach → YES  ("teach someone something")
  kill  → NO   (only one object)

Respond ONLY with JSON:
{"resultat": [{"id": <int>, "transitiv": <true|false>, "ditransitiv": <true|false>}]}
""",
    },

    'Substantiv': {
        'ordklass': 'Substantiv',
        'kolumn': 'räknebar',
        'prompt_extra': """
You are classifying nouns for a multilingual language learning system.
Use the translations (sv/en/fr/de) to identify the exact meaning being represented.

RÄKNEBAR — whether the noun can be counted (has both singular and plural):
  true  : countable, has plural forms      ("stol/chair → stolar/chairs")
  false : mass noun or abstract, no natural plural ("mjölk/milk, frihet/freedom")

Rules:
- When a word can be BOTH (e.g. "glass/glas" = drinking glass OR the material):
  use the meaning shown by the translations to decide
- Respond ONLY with JSON in this exact format:
  {"resultat": [{"id": <int>, "räknebar": <true|false>}]}
""",
    },
}

# ── Databas ───────────────────────────────────────────────────────────────────

def hämta_otaggade(con, ordklass, kolumn, custom_filter=None):
    filt = custom_filter if custom_filter else f'{kolumn} IS NULL'
    cur  = con.cursor()
    cur.execute(f'''
        SELECT k.id, k.namn,
               GROUP_CONCAT(l.språk || ':' || l.lemma, '|') AS översättningar
        FROM Koncept k
        LEFT JOIN Lexem l ON l.koncept_id = k.id AND l.språk IN ('sv','en','fr','de')
        WHERE k.ordklass = ? AND {filt}
        GROUP BY k.id
        ORDER BY k.id
    ''', (ordklass,))
    return cur.fetchall()

def spara_resultat(con, ordklass, kolumn, kid, värde, dry_run):
    """Spara ett värde (int eller bool) till specifik kolumn"""
    if not dry_run:
        con.execute(f'UPDATE Koncept SET {kolumn} = ? WHERE id = ?', (värde, kid))

def spara_rätta_valens(con, kid, transitiv, ditransitiv, dry_run):
    """OR:a in TRANSITIV och/eller DITRANSITIV utan att ta bort befintliga flaggor"""
    tillägg = 0
    if transitiv:
        tillägg |= Valens.TRANSITIV
    if ditransitiv:
        tillägg |= Valens.TRANSITIV | Valens.DITRANSITIV
    if tillägg and not dry_run:
        con.execute('UPDATE Koncept SET valens = valens | ? WHERE id = ?', (int(tillägg), kid))

# ── Ollama ────────────────────────────────────────────────────────────────────

def bygg_prompt(config, batch):
    extra = config['prompt_extra'].strip()

    koncept_json = []
    for (kid, namn, övers) in batch:
        transl = {}
        if övers:
            for par in övers.split('|'):
                if ':' in par:
                    lang, lemma = par.split(':', 1)
                    transl[lang] = lemma
        koncept_json.append({'id': kid, **transl})

    return f"""{extra}

Concepts to classify:
{json.dumps(koncept_json, ensure_ascii=False)}"""


def fråga_ollama(prompt):
    payload = {
        "model":    MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
        "format":   "json",
        "options":  {"temperature": 0.1},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    return json.loads(r.json()['message']['content'])

# ── Konvertera resultat till bitmask eller bool ────────────────────────────────

def flaggor_till_int(ordklass, kolumn, flaggnamn_lista):
    """Konvertera lista av flaggnamn till bitmask (för Verb) eller bool (för Substantiv)"""
    if ordklass == 'Substantiv':
        # räknebar är boolean
        if kolumn == 'räknebar':
            return 1 if (flaggnamn_lista == True or flaggnamn_lista == 1) else 0
    else:
        # Verb: valens och personlighet är bitmasks
        if kolumn == 'valens':
            klass = Valens
        elif kolumn == 'personlighet':
            klass = Personlighet
        else:
            return 0

        värde = 0
        for namn in (flaggnamn_lista if isinstance(flaggnamn_lista, list) else []):
            if hasattr(klass, namn):
                värde |= klass[namn]
        return värde or None

    return None

# ── Progressbar ───────────────────────────────────────────────────────────────

def progressbar(klar, total, bredd=28):
    andel = klar / total if total else 0
    fylld = int(andel * bredd)
    bar   = '█' * fylld + '░' * (bredd - fylld)
    return f'[{bar}] {klar:>4}/{total} ({andel*100:>3.0f}%)'

# ── Huvudloop ─────────────────────────────────────────────────────────────────

def kör(ordklass, kolumn, config, batch_storlek, dry_run, db_path=None):
    con = sqlite3.connect(db_path or DEFAULT_DB)
    rätta_läge = config.get('rätta', False)
    try:
        rader = hämta_otaggade(con, ordklass, kolumn, config.get('custom_filter'))
        total = len(rader)
        if total == 0:
            print(f'[{ordklass}:{kolumn}] Inga otaggade koncept — hoppar över.')
            return

        antal_batchar = math.ceil(total / batch_storlek)
        print(f'\n[{ordklass}:{kolumn}] {total} koncept → {antal_batchar} batchar om max {batch_storlek}')
        if dry_run:
            print('  (dry-run: inga ändringar sparas)')

        klar  = 0
        tider = []
        fel   = 0

        for i in range(antal_batchar):
            batch = rader[i * batch_storlek:(i + 1) * batch_storlek]

            eta_str = '?'
            if tider:
                snitt   = sum(tider) / len(tider)
                kvar    = snitt * (antal_batchar - i)
                eta_str = f'{int(kvar // 60)}m{int(kvar % 60):02d}s'

            print(f'\r  Batch {i+1:>3}/{antal_batchar}  {progressbar(klar, total)}  ETA {eta_str}   ',
                  end='', flush=True)

            t0       = time.time()
            resultat = []
            for försök in range(3):
                try:
                    svar     = fråga_ollama(bygg_prompt(config, batch))
                    resultat = svar.get('resultat', [])
                    break
                except Exception as e:
                    if försök == 2:
                        print(f'\n  ✗ Batch {i+1} misslyckades: {e}')
                        fel += len(batch)
                    else:
                        time.sleep(2)

            svar_map = {r['id']: r for r in resultat if isinstance(r, dict)}

            for (kid, namn, _) in batch:
                post = svar_map.get(kid, {})

                if rätta_läge:
                    # OR-uppdatering: lägg till TRANSITIV/DITRANSITIV om de saknas
                    spara_rätta_valens(con, kid,
                                       post.get('transitiv', False),
                                       post.get('ditransitiv', False),
                                       dry_run)
                elif kolumn == 'räknebar':
                    räknebar_val = post.get('räknebar', True)
                    spara_resultat(con, ordklass, kolumn, kid, räknebar_val, dry_run)
                else:
                    # Bitmask (valens eller personlighet)
                    flaggor = post.get(kolumn, [])
                    värde = flaggor_till_int(ordklass, kolumn, flaggor)
                    spara_resultat(con, ordklass, kolumn, kid, värde, dry_run)

                klar += 1

            if not dry_run:
                con.commit()

            elapsed = time.time() - t0
            tider.append(elapsed)
            if len(tider) > 10:
                tider.pop(0)

        print(f'\r  Klart!  {progressbar(klar, total)}  ({fel} fel)          ')

    finally:
        con.close()

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Taggar grammatiska egenskaper via Ollama')
    parser.add_argument('--ordklass', choices=['Verb', 'Substantiv', 'alla'], default='alla',
                        help='Vilken ordklass att tagga (standard: alla)')
    parser.add_argument('--aspekt', choices=['valens', 'personlighet', 'rätta'], default=None,
                        help='För Verb: vilken aspekt. "rätta" korrigerar INTRANSITIV-only verb.')
    parser.add_argument('--batch', type=int, default=25,
                        help='Antal koncept per prompt (standard: 25)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Kör utan att spara till databasen')
    parser.add_argument('--db', default=None,
                        help='Sökväg till databas (standard: ordbok/ord.db)')
    args = parser.parse_args()

    try:
        requests.get('http://localhost:11434', timeout=3)
    except Exception:
        print('Fel: Ollama svarar inte på http://localhost:11434')
        print('Starta med: ollama serve')
        sys.exit(1)

    # Bestäm vilka ordklasser/aspekter som ska köras
    ordklasser_att_köra = []

    if args.ordklass == 'alla':
        ordklasser_att_köra = ['Verb_valens', 'Verb_personlighet', 'Substantiv']
    elif args.ordklass == 'Verb':
        if args.aspekt:
            ordklasser_att_köra = [f'Verb_{args.aspekt}']
        else:
            ordklasser_att_köra = ['Verb_valens', 'Verb_personlighet', 'Verb_rätta']
    elif args.ordklass == 'Substantiv':
        ordklasser_att_köra = ['Substantiv']

    for ok_key in ordklasser_att_köra:
        config = ORDKLASSER[ok_key]
        ordklass = config['ordklass']
        kolumn = config['kolumn']
        kör(ordklass, kolumn, config, args.batch, args.dry_run, db_path=args.db)

    print('\nKlart!')

if __name__ == '__main__':
    main()
