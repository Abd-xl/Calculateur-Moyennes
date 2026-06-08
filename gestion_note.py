from sauvegarde import sauvegarder
from sauvegarde import notes, coef

def calculer_moyenne(liste_notes):
    if len(liste_notes) == 0:
        return 0
    return sum(liste_notes) / len(liste_notes)

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


def voir_notes():
    if not notes:
        print('Aucune note enregistrée. ')
        return

    print('\n--- Notes par matiere ---')
    for matiere in notes:
        print(f'\n  {matiere} : ')
        for note in notes[matiere]:
            print(f'  {note}/20')


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


def supprimer_matiere():
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

