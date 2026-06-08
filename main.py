from gestion_note import ajouter_notes, voir_moyenne, voir_notes, menu_modifier
from sauvegarde import charger, reinitialiser

def afficher_menu():
    print('\n--- MENU ---')
    print('1. Ajouter des notes')
    print('2. Voir les moyennes')
    print('3. Voir les notes')
    print('4. Reinitialiser')
    print('5. Modifier')
    print('6. Quitter')

def main():
    charger()
    print('---------Welcome to the note calculator------------')

while True:
    afficher_menu()
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

if __name__ == "__main__":
    main()


