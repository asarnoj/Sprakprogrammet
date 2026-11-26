#!/usr/bin/env python3
"""
omtagga_flaggor.py — Nollar och kör om specifika flaggor med skarpare prompter.

Används för att rätta systematiska fel från tagga_semantik.py.
Övriga flaggor på varje koncept bevaras — bara de angivna flaggorna skrivs om.

Kör:
    python3 omtagga_flaggor.py              # kör om ÄTBAR och RÖRELSE (standard)
    python3 omtagga_flaggor.py --dry-run    # visa utan att spara
"""

import sqlite3, json, requests, argparse, sys, time, math
from bitflaggor import SubstantivSemantics

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen2.5:7b"
DB_PATH    = "ordbok/ord.db"

# ── Skärpta definitioner för de flaggor som hade systematiska fel ─────────────

PROMPT_ÄTBAR = """You are classifying nouns. Answer ONLY whether each concept is literally edible or drinkable.

ÄTBAR = Yes ONLY if:
- It is food that humans eat (bread, apple, rice, meat, cheese, salad)
- It is a beverage that humans drink (water, wine, juice, tea, coffee, beer)
- It is a food ingredient or seasoning (salt, sugar, flour, oil, spice)

ÄTBAR = No if it is:
- A container or appliance (bottle, fridge, tin can)
- A financial concept (tax, fee, money, income, cost, rent, grant)
- An abstract concept (advertising, learning, formula, brand)
- A material or substance that isn't food (metal, leather, coal, cotton)
- A living creature (spider, lion — even if technically edible)
- An activity or event (meal is ÄTBAR, but eating as activity is not)
- Anything else that isn't literally consumed as food or drink

Respond ONLY with:
{{"resultat": [{{"id": <int>, "ÄTBAR": true|false}}]}}

Concepts:
{koncept_json}"""

PROMPT_RÖRELSE = """You are classifying nouns. Answer ONLY whether each concept is a physical object or entity that moves through space.

RÖRELSE = Yes ONLY if:
- It is a vehicle or vessel (car, boat, train, aircraft, bicycle)
- It is a natural force or flow that moves (river, wind, current, wave, flood)
- It is an animal or creature (already tagged elsewhere — say No here)
- It is something that physically travels or is propelled (rocket, arrow, ball in flight)

RÖRELSE = No if it is:
- A stationary object (bridge, building, door, wall)
- An abstract concept (action, haste, movement as idea, notice, learning)
- A process or activity (heating, printing, washing, race as event)
- A body part
- A feeling, idea, or institution

Respond ONLY with:
{{"resultat": [{{"id": <int>, "RÖRELSE": true|false}}]}}

Concepts:
{koncept_json}"""

# ── Databas ───────────────────────────────────────────────────────────────────

def hämta_med_flagga(con, bit):
    """Hämta alla substantiv som har angiven bit satt."""
    cur = con.cursor()
    cur.execute('''
        SELECT k.id, k.namn, k.semantik,
               GROUP_CONCAT(l.språk || ':' || l.lemma, '|') AS översättningar
        FROM Koncept k
        LEFT JOIN Lexem l ON l.koncept_id = k.id AND l.språk IN ('sv','en','fr','de')
        WHERE k.ordklass = 'Substantiv' AND k.semantik & ? = ?
        GROUP BY k.id
        ORDER BY k.id
    ''', (bit, bit))
    return cur.fetchall()

def rensa_bit(con, koncept_id, bit):
    """Ta bort en specifik bit från semantik utan att röra övriga."""
    con.execute(
        'UPDATE Koncept SET semantik = semantik & ? WHERE id = ?',
        (~bit & 0xFFFFFFFF, koncept_id)
    )

def sätt_bit(con, koncept_id, bit):
    con.execute(
        'UPDATE Koncept SET semantik = semantik | ? WHERE id = ?',
        (bit, koncept_id)
    )

# ── Ollama ────────────────────────────────────────────────────────────────────

def bygg_koncept_json(batch):
    resultat = []
    for (kid, namn, _, övers) in batch:
        transl = {}
        if övers:
            for par in övers.split('|'):
                if ':' in par:
                    lang, lemma = par.split(':', 1)
                    transl[lang] = lemma
        resultat.append({'id': kid, **transl})
    return json.dumps(resultat, ensure_ascii=False)

def fråga_ollama(prompt):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    return json.loads(r.json()['message']['content'])

# ── Progressbar ───────────────────────────────────────────────────────────────

def progressbar(klar, total, bredd=28):
    andel = klar / total if total else 0
    fylld = int(andel * bredd)
    return f'[{"█"*fylld}{"░"*(bredd-fylld)}] {klar:>4}/{total} ({andel*100:>3.0f}%)'

# ── Huvudloop för en flagga ───────────────────────────────────────────────────

def kör_flagga(flaggnamn, prompt_mall, bit, batch_storlek, dry_run):
    con = sqlite3.connect(DB_PATH)
    try:
        rader = hämta_med_flagga(con, bit)
        total = len(rader)
        if total == 0:
            print(f'[{flaggnamn}] Inga koncept med denna flagga hittades.')
            return

        antal_batchar = math.ceil(total / batch_storlek)
        print(f'\n[{flaggnamn}] {total} koncept att granska → {antal_batchar} batchar')
        if dry_run:
            print('  (dry-run: inga ändringar sparas)')

        klar  = 0
        tider = []
        behåll = 0
        ta_bort = 0

        for i in range(antal_batchar):
            batch = rader[i * batch_storlek:(i + 1) * batch_storlek]

            eta_str = '?'
            if tider:
                snitt   = sum(tider) / len(tider)
                kvar    = snitt * (antal_batchar - i)
                eta_str = f'{int(kvar//60)}m{int(kvar%60):02d}s'

            print(f'\r  Batch {i+1:>3}/{antal_batchar}  {progressbar(klar, total)}  ETA {eta_str}   ', end='', flush=True)

            t0 = time.time()
            koncept_json = bygg_koncept_json(batch)
            prompt = prompt_mall.format(koncept_json=koncept_json)

            svar_map = {}
            for försök in range(3):
                try:
                    svar = fråga_ollama(prompt)
                    for r in svar.get('resultat', []):
                        svar_map[r['id']] = r.get(flaggnamn, True)
                    break
                except Exception as e:
                    if försök == 2:
                        print(f'\n  ✗ Batch {i+1} misslyckades: {e}')
                    else:
                        time.sleep(2)

            for (kid, namn, _, _) in batch:
                behåll_flagga = svar_map.get(kid, True)  # behåll vid osäkerhet
                if behåll_flagga:
                    behåll += 1
                else:
                    ta_bort += 1
                    if not dry_run:
                        rensa_bit(con, kid, bit)
                klar += 1

            if not dry_run:
                con.commit()

            tider.append(time.time() - t0)
            if len(tider) > 10:
                tider.pop(0)

        print(f'\r  Klart!  {progressbar(klar, total)}                              ')
        print(f'  Behållit: {behåll}  |  Borttaget: {ta_bort}')

    finally:
        con.close()

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Kör om specifika semantikflaggor med skarpare prompter')
    parser.add_argument('--batch', type=int, default=20)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    try:
        requests.get('http://localhost:11434', timeout=3)
    except Exception:
        print('Fel: Ollama svarar inte. Starta med: ollama serve')
        sys.exit(1)

    kör_flagga('ÄTBAR',  PROMPT_ÄTBAR,  int(SubstantivSemantics.ÄTBAR),  args.batch, args.dry_run)
    kör_flagga('RÖRELSE', PROMPT_RÖRELSE, int(SubstantivSemantics.RÖRELSE), args.batch, args.dry_run)

    print('\nKlart! Kör gärna en kontroll efteråt:')
    print('  python3 -c "from bitflaggor import SubstantivSemantics; import sqlite3; ...')

if __name__ == '__main__':
    main()
