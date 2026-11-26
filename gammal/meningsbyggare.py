from fraser import Sats

def skapa_meny(lager):
    dict = lager.generera_dict()
    antal_val = len(dict)

    for i, (slot, metod) in enumerate(dict.items(), start=1):
        if metod[0]:
            print(f"{i}. Redigera {slot} ({metod[0]})")
        else:
            print(f"{i}. Skapa {slot}")

    if lager.förälder:
        print(f"{antal_val + 1}. Tillbaka")
    else:
        print(f"{antal_val + 1}. Avsluta")

    val = int(input(f"Välj ett alternativ (1 - {antal_val + 1}): "))

    if val == antal_val + 1 and lager.förälder:
        return lager.förälder
    elif val == antal_val + 1:
        exit()
    else:
        lager = list(dict.values())[val - 1][1]()

    return lager

språk = input("Välj språk (sv/en/de/fr/es/it/ja): ").strip() or 'sv'
lager = Sats(språk=språk)

while True:
    lager = skapa_meny(lager)
    print(f"\nlager: {lager}") 