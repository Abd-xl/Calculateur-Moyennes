import json

#--- Variables ----
notes = {}
coef = {}

#--- Fonctions ----

def calculer_moyenne(liste_notes):
    return sum(liste_notes) / len(liste_notes)

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

# --- Menus ----

def ajouter_notes():
    while True:
        matiere = input('\nMatiere (ou fin pour terminer) :')
        if matiere.lower() == 'fin':
            break
        if matiere not in notes:
            notes[matiere] = []
            while True:
               try:
                   coef[matiere] = int(input(f'Coefficient {matiere} :'))
                   break
               except ValueError:
                print('Veuillez entrez un nombre entier.')

        while True:
            try:
                nb = int(input(f'Combien de notes en {matiere} ?'))
                break
            except ValueError:
                print('Veuillez entrez un nombre entier.')

        for i in range(nb):
            while True:
                try:
                    note = float(input(f'   Note {i + 1} : '))
                    if 0 <= note <= 20:
                        notes[matiere].append(note)
                        break
                    else:
                        print('Hum please mets ta vrai note !')
                except ValueError:
                    print('Veuillez entrez un nombre valide.')

        sauvegarder()
        print(f'Ok Notes de {matiere} enregistrées.')

def voir_moyenne():
    if not notes:
        print('Aucune note enregistrée.')
        return

    print('\n--- Moyennes par matiere ---')
    somme_ponderee = 0
    somme_coef = 0

    for matiere in notes:
        moy = calculer_moyenne(notes[matiere])
        print(f'  {matiere} (coeff. {coef[matiere]}) : {moy:.2f}/20')
        somme_ponderee += moy*coef[matiere]
        somme_coef += coef[matiere]

    print(f'\n  Moyenne Generale : {somme_ponderee /somme_coef:.2f}/20')

def voir_notes():
    if not notes:
        print('Aucune note enregistrée. ')
        return

    print('\n--- Notes par matiere ---')
    for matiere in notes:
        print(f'\n  {matiere} : ')
        for note in notes[matiere]:
            print(f'  {note}/20')

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

def supprimer_matiere():
    global notes, coef
    while True:
        print('Liste des matieres')
        for matiere in notes:
            print(f'  {matiere} ')
        matiere = input('\nQuel matiere ?(Ou fin pour annuler) : ')
        if matiere in notes:
            del notes[matiere]
            del coef[matiere]
            sauvegarder()
            print(f'{matiere} is clear')
            break
        elif matiere.lower() == 'fin':
            break
        else:
             print(f"{matiere} n'existe pas")

def supprimer_notes():
    global notes, coef
    voir_notes()
    while True:

        matiere = str(input('\nDans quel matiere ? (ou fin) : '))

        if matiere.lower() == 'fin':
            break
        elif not matiere in notes:
            print(f'{matiere} n\'existe pas')
            continue
        while True:
            try:
                supp = float(input(f'Quel note de {matiere} veut tu supprimer ? '))
            except ValueError:
                print('What have you done')
                continue
            if not notes[matiere]:
                print(f"{matiere} est vide ")
                break
            elif not supp in notes[matiere]:
                print(f"{supp} n'existe pas dans {matiere}")
                continue
            elif supp in notes[matiere]:
                notes[matiere].remove(supp)
                print(f'{supp} is removed ')
                sauvegarder()
                voir_notes()
                break
            else:
                 print('error')



def menu_modifier():
    while True:
        print("---- Modifier / Supprimer ----")
        print('1. Supprimer une matiere')
        print('2. Supprimer une note')
        print('3. Modifier une note (dont work yet)')
        print('4. Retour')

        choix2 = input('\nVotre choix ? : ')
        if choix2 == '1':
            supprimer_matiere()
        elif choix2 == '2':
            supprimer_notes()
        elif choix2 == '3':
            pass
        elif choix2 == '4':
            break
        else:
            print('Choix invalide')



# --- Demarage ----

charger()
print('---------Welcome to the note calculator------------')

while True:
    print('\n--- MENU ---')
    print('1. Ajouter des notes')
    print('2. Voir les moyennes')
    print('3. Voir les notes')
    print('4. Reinitialiser')
    print('5. Modifier')
    print('6. Quitter')

    choix = input('\nVotre choix ? : ')

    if choix == '1':
        ajouter_notes()
    elif choix == '2':
        voir_moyenne()
    elif choix == '3':
        voir_notes()
    elif choix == '4':
        reinitialiser()
    elif choix == '5':
        menu_modifier()
    elif choix == '6':
        print('See you soon!')
        break
    else:
        print('Choix invalide')



