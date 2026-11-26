import sqlite3
import random

db = sqlite3.connect("ordbok/sprak.db")

kartor = {
    "numerus": {1: "Singular", 2: "Plural"},
    "species": {1: "Obestämd", 2: "Bestämd"},
    "kasus":   {1: "Nominativ", 2: "Ackusativ", 4: "Dativ", 8: "Genitiv"},
    "genus":   {1: "Utrum/Maskulin", 2: "Neutrum/Feminin"},
    "tempus":  {"infinitiv": "Infinitiv", "presens": "Presens", "preteritum": "Preteritum",
                "supinum": "Supinum", "imperativ": "Imperativ",
                "perfekt particip": "Perfekt particip", "presens particip": "Presens particip"},
    "grad":    {"Positiv": "Positiv", "Komparativ": "Komparativ", "Superlativ": "Superlativ"}
}

def hämta_slumpmässigt_koncept_id(ordklass: str) -> int:
    sql = "SELECT id FROM Koncept WHERE ordklass = ? ORDER BY RANDOM() LIMIT 1"
    return db.execute(sql, (ordklass,)).fetchone()[0]

def hämta_lexem_id(koncept_id: int, språk: str) -> int:
    sql = "SELECT id FROM Lexem WHERE koncept_id = ? AND språk = ?"
    return db.execute(sql, (koncept_id, språk)).fetchone()[0]

def hämta_form(lexem_id: int, numerus=None, species=None, kasus=None, genus=None, tempus=None, grad=None, person=None) -> str:
    villkor = [f"lexem_id = {lexem_id}"]

    # numerus, species, genus: NULL i DB = formen gäller oavsett denna dimension
    # (t.ex. adjektiv-superlativ "vackraste" har numerus=NULL = gäller sg och pl)
    for kolumn, värde in [("numerus", numerus), ("species", species)]:
        if värde is not None:
            villkor.append(f"({kolumn} = {värde} OR {kolumn} IS NULL)")

    if genus is not None:
        villkor.append(f"(genus = {genus} OR genus IS NULL)")

    # person: exakt matchning — personböjda former ska inte matcha fel person
    if person is not None:
        villkor.append(f"person = {person}")

    # kasus: bitflagg — NULL i DB = formen gäller oavsett kasus (t.ex. svenska/franska substantiv)
    if kasus is not None:
        villkor.append(f"(kasus & {int(kasus)} OR kasus IS NULL)")

    # tempus: bitmask — raden matchar om den täcker det efterfrågade tempuset
    # (t.ex. svenska "åt" har tempus=36 = 4|32, matchar både PRETERITUM=4 och PRETERITUM_PERFEKT=32)
    if tempus is not None:
        villkor.append(f"tempus & {int(tempus)}")

    # grad: exakt matchning (ett adjektiv är antingen positiv, komparativ eller superlativ)
    if grad is not None:
        villkor.append(f"grad = {int(grad)}")

    # Hämta form + alla dimensionskolumner för att kunna detektera tvetydighet
    sql = ("SELECT form, numerus, species, kasus, genus, tempus, grad, person "
           "FROM Former WHERE " + " AND ".join(villkor))
    rader = db.execute(sql).fetchall()

    if not rader:
        return None

    if len(rader) == 1:
        return rader[0][0]

    # Flera rader matchar — identifiera vilka ospecificerade parametrar som varierar
    KOLUMN_INDEX = {"numerus": 1, "species": 2, "kasus": 3, "genus": 4,
                    "tempus": 5, "grad": 6, "person": 7}
    inskickade = {"numerus": numerus, "species": species, "kasus": kasus,
                  "genus": genus, "tempus": tempus, "grad": grad, "person": person}

    ospecificerade = [
        kolumn
        for kolumn, värde in inskickade.items()
        if värde is None
        and len({rad[KOLUMN_INDEX[kolumn]] for rad in rader}) > 1
    ]

    former = [rad[0] for rad in rader]
    vald   = random.choice(former)

    print(f"  ⚠  Tvetydig form för lexem_id={lexem_id}: "
          f"{', '.join(ospecificerade)} ej specificerade. "
          f"Möjliga: {former}. "
          f"Valde: '{vald}'.")

    return vald

def visa_lemma(koncept_id: int, språk: str = 'sv') -> str:
    lexem_id = hämta_lexem_id(koncept_id, språk)
    sql = "SELECT lemma FROM Lexem WHERE id = ?"
    return db.execute(sql, (lexem_id,)).fetchone()[0]

# Egenskaper som numera bor i Koncept (språkoberoende)
_KONCEPT_KOLUMNER = {'ordklass', 'valens', 'personlighet', 'gradbarhet',
                     'person', 'numerus', 'räknebar', 'semantik'}

def kolla_lexems_egenskap(lexem_id: int, parameter: str):
    """Slår upp en egenskap via lexem_id. Routar automatiskt till Koncept
    för språkoberoende kolumner, annars till Lexem."""
    if parameter in _KONCEPT_KOLUMNER:
        sql = (f"SELECT Koncept.{parameter} FROM Koncept "
               f"JOIN Lexem ON Lexem.koncept_id = Koncept.id "
               f"WHERE Lexem.id = ?")
    else:
        sql = f"SELECT {parameter} FROM Lexem WHERE id = ?"
    return db.execute(sql, (lexem_id,)).fetchone()[0]

def hämta_slot_frastyp(koncept_id: int, slot: str) -> int:
    """Returnerar frastyp-bitmask för given slot från MönsterKrav, eller 0 om inget krav finns."""
    sql = """
        SELECT MK.frastyp
        FROM MönsterKrav MK
        JOIN Mönster M ON M.id = MK.mönster_id
        WHERE M.koncept_id = ? AND MK.slot = ? AND MK.frastyp IS NOT NULL
        LIMIT 1
    """
    rad = db.execute(sql, (koncept_id, slot)).fetchone()
    return rad[0] if rad else 0

def kolla_forms_egenskap(form_id: int, parameter: str) -> str:
    sql = f"SELECT {parameter} FROM Former WHERE id = {form_id}"
    egenskap_int = db.execute(sql).fetchone()[0]
    karta = kartor.get(parameter)
    värden = []
    for bit, namn in karta.items():
        if (egenskap_int & bit):
            värden.append(namn)
    return ", ".join(värden)
