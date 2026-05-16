import json

print('Welcome to the note calculator')

def calculer_moyenne(liste_notes):
    return sum(liste_notes) / len(liste_notes)

notes = {}
coef = {}

def sauvegarder():
    with open('notes.json' , 'w') as f:
        json.dump({'notes': notes, 'coef': coef}, f)

def charger():
    global notes, coef
    try:
        with open('notes.json', 'r') as f:
            data = json.load(f)
            notes = data['notes']
            coef = data['coef']
    except FileNotFoundError:
        pass

def ajouter_notes():
    while True:
        matiere = input('Matiere (ou fin pour arreter) ')
        if matiere.lower() == 'fin':
            break
        if matiere not in notes:
            notes[matiere] = []
            while True:
               try:
                   coef[matiere] = int(input(f'Coefficient {matiere} :'))
                   break
               except ValueError:
                print('Entrez un nombre entier.')

        while True:
            try:
                nb = int(input(f'Combien de notes en {matiere} ?'))
                break
            except ValueError:
                print('Choisissez un numero')
        for i in range(nb):
            while True:
                try:
                    note = float(input(f'Note {i + 1} :'))
                    if 0 <= note <= 20:
                        notes[matiere].append(note)
                        break
                    else:
                        print('Note invalide')
                except ValueError:
                    print('Choisissez un numero')
        sauvegarder()


def voir_moyenne():
    if not notes:
        print('Aucune note enregistrée')
        return
    somme_ponderee = 0
    somme_coef = 0
    for matiere in notes:
        moy = calculer_moyenne(notes[matiere])
        print(f'{matiere} : {moy:.2f}')

        somme_ponderee += moy*coef[matiere]
        somme_coef += coef[matiere]
    print(f'Moyenne Generale : {somme_ponderee /somme_coef:.2f}')

charger()

while True:
    print('\n--- MENU ---')
    print('1. ajouter des notes')
    print('2. Voir les moyennes')
    print('3. Quiter')
    choix = input('Choisissez un choix : ')

    if choix == '1':
        ajouter_notes()
    elif choix == '2':
        voir_moyenne()
    elif choix == '3':
        print('BYE')
        break
    else:
        print('Choisissez un choix : ')



