from gestion_note import (
    _trouver_matiere,
    ajouter_note,
    calculer_moyennes,
    modifier_note,
    supprimer_matiere,
    supprimer_note,
    notes,
    coef,
)
from sauvegarde import charger, reinitialiser


def ajouter_notes():
    while True:
        matiere = input("\nMatiere (ou fin pour terminer) :")
        if matiere.lower() == "fin":
            break

        matiere_existante = _trouver_matiere(matiere)
        if matiere_existante is not None:
            matiere = matiere_existante
            coefficient = coef[matiere]
        else:
            while True:
                try:
                    coefficient = int(input(f"Coefficient {matiere} :"))
                    break
                except ValueError:
                    print("Veuillez entrez un nombre entier.")

        while True:
            try:
                nb = int(input(f"Combien de notes en {matiere} ?"))
                if nb < 0:
                    raise ValueError
                break
            except ValueError:
                print("Veuillez entrez un nombre entier positif.")

        for i in range(nb):
            while True:
                try:
                    note = float(input(f"   Note {i + 1} : "))
                    ajouter_note(matiere, note, coefficient)
                    break
                except (TypeError, ValueError) as erreur:
                    print(erreur)

        print(f"Ok Notes de {matiere} enregistrées.")


def voir_notes():
    if not notes:
        print("Aucune note enregistrée.")
        return

    print("\n--- Notes par matiere ---")
    for matiere in notes:
        print(f"\n  {matiere} :")
        for note in notes[matiere]:
            print(f"  {note['note']}/{note['bareme']}")


def voir_moyenne():
    if not notes:
        print("Aucune note enregistrée.")
        return

    moyennes, moyenne_generale = calculer_moyennes()
    print("\n--- Moyennes par matiere ---")
    for matiere, moyenne in moyennes.items():
        print(f"  {matiere} (coeff. {coef[matiere]}) : {moyenne:.2f}/20")
    print(f"\n  Moyenne Generale : {moyenne_generale:.2f}/20")


def menu_supprimer_matiere():
    while True:
        print("Liste des matieres")
        for matiere in notes:
            print(f"  {matiere}")

        matiere = input("\nQuelle matiere ? (ou fin pour annuler) : ")
        if _trouver_matiere(matiere) is not None:
            try:
                supprimer_matiere(matiere)
                print(f"{matiere} is clear")
                break
            except ValueError as erreur:
                print(erreur)
        elif matiere.lower() == "fin":
            break
        else:
            print(f"{matiere} n'existe pas")


def supprimer_notes():
    voir_notes()
    while True:
        matiere = input("\nDans quelle matiere ? (ou fin) : ")
        if matiere.lower() == "fin":
            break
        if _trouver_matiere(matiere) is None:
            print(f"{matiere} n'existe pas")
            continue

        while True:
            try:
                index = int(input("Index de la note à supprimer : "))
                supprimer_note(matiere, index)
                print("Note supprimée")
                voir_notes()
                break
            except (TypeError, ValueError) as erreur:
                print(erreur)


def menu_modifier():
    while True:
        print("---- Modifier / Supprimer ----")
        print("1. Supprimer une matiere")
        print("2. Supprimer une note")
        print("3. Modifier une note")
        print("4. Retour")

        choix2 = input("\nVotre choix ? : ")
        if choix2 == "1":
            menu_supprimer_matiere()
        elif choix2 == "2":
            supprimer_notes()
        elif choix2 == "3":
            matiere = input("Matiere : ")
            try:
                index = int(input("Index de la note : "))
                nouvelle_note = float(input("Nouvelle note : "))
                modifier_note(matiere, index, nouvelle_note)
                print("Note modifiee.")
            except (TypeError, ValueError) as erreur:
                print(erreur)
        elif choix2 == "4":
            break
        else:
            print("Choix invalide")


def afficher_menu():
    print("\n--- MENU ---")
    print("1. Ajouter des notes")
    print("2. Voir les moyennes")
    print("3. Voir les notes")
    print("4. Reinitialiser")
    print("5. Modifier")
    print("6. Quitter")


def main():
    charger()
    print("---------Welcome to the note calculator------------")

    while True:
        afficher_menu()
        choix = input("\nVotre choix ? : ")
        if choix == "1":
            ajouter_notes()
        elif choix == "2":
            voir_moyenne()
        elif choix == "3":
            voir_notes()
        elif choix == "4":
            reinitialiser()
        elif choix == "5":
            menu_modifier()
        elif choix == "6":
            print("See you soon!")
            break
        else:
            print("Choix invalide")


if __name__ == "__main__":
    main()
