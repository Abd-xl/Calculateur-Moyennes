import json

notes = {}
coef = {}

def sauvegarder():
    try:
        with open('notes.json' , 'w') as f:
            json.dump({'notes': notes, 'coef': coef}, f)
            print("Données sauvegardées avec succès.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données : {e}")


def charger():
    global notes, coef
    try:
        with open('notes.json', 'r') as f:
            data = json.load(f)
            notes.update(data.get("notes", {}))
            coef.update(data.get("coef", {}))
            print("Données chargées avec succès.")
    except FileNotFoundError:
        pass

def reinitialiser():
    global notes, coef
    comfirmation = input('\nVoulez vous reinitialiser ? y/n: ')
    if comfirmation.lower() == 'y':
        notes.clear()
        coef.clear()
        sauvegarder()
        print('Success')
    elif comfirmation.lower() == 'n':
        print('Annulé.')