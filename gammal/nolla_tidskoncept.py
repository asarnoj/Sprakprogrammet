#!/usr/bin/env python3
"""
nolla_tidskoncept.py — Nollar semantik för tidskoncept så att tagga_semantik.py kan köra om dem.

Kör efter att tagga_semantik.py är klar:
    python3 nolla_tidskoncept.py            # visar vad som skulle nollas
    python3 nolla_tidskoncept.py --verkställ  # nollar på riktigt
"""

import sqlite3, argparse

DB_PATH = "ordbok/ord.db"

# Ord vars engelska namn tyder på tidskoncept
TIDSORD = {
    'afternoon', 'age', 'ancient', 'april', 'august', 'autumn', 'century',
    'childhood', 'christmas', 'date', 'dawn', 'day', 'daybreak', 'daytime',
    'decade', 'december', 'dusk', 'early', 'easter', 'epoch', 'era',
    'evening', 'february', 'future', 'hour', 'instant', 'january', 'july',
    'june', 'lunchtime', 'march', 'may', 'midnight', 'millennium', 'minute',
    'moment', 'monday', 'month', 'morning', 'night', 'noon', 'november',
    'october', 'past', 'period', 'present', 'quarter', 'saturday', 'season',
    'second', 'september', 'spring', 'summer', 'sunday', 'thursday', 'time',
    'today', 'tomorrow', 'tuesday', 'tuesday', 'wednesday', 'week', 'weekend',
    'winter', 'year', 'yesterday', 'youth',
}

def hitta_tidskoncept(con):
    cur = con.cursor()
    cur.execute('''
        SELECT id, namn, semantik
        FROM Koncept
        WHERE ordklass = 'Substantiv'
          AND semantik IS NOT NULL
          AND LOWER(namn) IN ({})
    '''.format(','.join('?' * len(TIDSORD))), list(TIDSORD))
    return cur.fetchall()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verkställ', action='store_true',
                        help='Nolla på riktigt (utan flaggan visas bara vad som skulle nollas)')
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)

    träffar = hitta_tidskoncept(con)
    if not träffar:
        print('Inga taggade tidskoncept hittades.')
        con.close()
        return

    print(f'Hittade {len(träffar)} tidskoncept med semantik-värde:')
    for id_, namn, semantik in träffar:
        print(f'  {id_:>5}  {namn:<30}  semantik={semantik}')

    if args.verkställ:
        ids = [r[0] for r in träffar]
        con.executemany('UPDATE Koncept SET semantik = NULL WHERE id = ?', [(i,) for i in ids])
        con.commit()
        print(f'\nNollade {len(ids)} koncept. Kör nu: python3 tagga_semantik.py --ordklass Substantiv')
    else:
        print(f'\nInget ändrat. Kör med --verkställ för att nolla dessa och tagga om dem.')

    con.close()

if __name__ == '__main__':
    main()
