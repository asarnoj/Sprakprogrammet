"""
Språkprogrammet — interaktivt testgränssnitt.

Kör med:  python meny.py
"""

import inspect
import testmeningar
from renderare import rendera

SPRÅK = [
    ('sv', 'Svenska '),
    ('fr', 'Franska '),
]

BRED_SEPARATOR  = "═" * 46
TUNN_SEPARATOR  = "─" * 46


def hämta_testmeningar() -> list[tuple[str, callable]]:
    """Plockar automatiskt upp alla funktioner från testmeningar.py i källkod-ordning."""
    funktioner = inspect.getmembers(testmeningar, inspect.isfunction)
    # Sortera på rad-nummer så menyn följer filens ordning
    funktioner.sort(key=lambda nf: inspect.getsourcelines(nf[1])[1])
    return funktioner


def visa_meny(meningar: list[tuple[str, callable]]) -> None:
    print(f"\n{BRED_SEPARATOR}")
    print("  SPRÅKPROGRAMMET — välj en testmening")
    print(BRED_SEPARATOR)
    for i, (namn, funktion) in enumerate(meningar, start=1):
        beskrivning = (funktion.__doc__ or namn).strip()
        print(f"  {i:>2}.  {beskrivning}")
    print(TUNN_SEPARATOR)
    print("   0.  Visa alla")
    print("   q.  Avsluta")
    print(BRED_SEPARATOR)


def visa_översättningar(namn: str, funktion: callable) -> None:
    beskrivning = (funktion.__doc__ or namn).strip()
    print(f"\n{TUNN_SEPARATOR}")
    print(f"  {beskrivning}")
    print(TUNN_SEPARATOR)
    sats = funktion()
    for kod, etikett in SPRÅK:
        try:
            resultat = rendera(sats, kod)
        except Exception as fel:
            resultat = f"[fel: {fel}]"
        print(f"  {etikett}  {resultat}")
    print(TUNN_SEPARATOR)


def main() -> None:
    meningar = hämta_testmeningar()

    while True:
        visa_meny(meningar)
        try:
            val = input("\n  Ditt val: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Hej då!\n")
            break

        if val == 'q':
            print("\n  Hej då!\n")
            break

        if val == '0':
            print()
            for namn, funktion in meningar:
                visa_översättningar(namn, funktion)
            input("\n  [tryck Enter för att fortsätta]")
            continue

        if val.isdigit():
            index = int(val) - 1
            if 0 <= index < len(meningar):
                namn, funktion = meningar[index]
                visa_översättningar(namn, funktion)
                input("\n  [tryck Enter för att fortsätta]")
                continue

        print("\n  Ogiltigt val, försök igen.")


if __name__ == "__main__":
    main()
