from sauvegarde import sauvegarder
from sauvegarde import notes, coef


def calculer_moyenne(liste_notes):
    if len(liste_notes) == 0:
        return 0
    return sum(liste_notes) / len(liste_notes)


def ajouter_note(matiere, note, coefficient):
    if not matiere.strip():
        raise ValueError("La matière ne peut pas être vide.")

    if not isinstance(note, (int, float)):
        raise TypeError("La note doit être un nombre.")
    if not 0 <= note <= 20:
        raise ValueError("La note doit être comprise entre 0 et 20.")

    if not isinstance(coefficient, int):
        raise TypeError("Le coefficient doit être un entier.")
    if coefficient <= 0:
        raise ValueError("Le coefficient doit être supérieur à 0.")

    if matiere not in notes:
        notes[matiere] = []
        coef[matiere] = coefficient
    elif coef[matiere] != coefficient:
        raise ValueError(
            f"La matière existe déjà avec le coefficient {coef[matiere]}."
        )

    notes[matiere].append(note)
    sauvegarder()


def modifier_note(matiere, ancienne_note, nouvelle_note):
    if matiere not in notes:
        raise ValueError("Cette matière n'existe pas.")

    if not 0 <= nouvelle_note <= 20:
        raise ValueError("La nouvelle note doit être comprise entre 0 et 20.")

    if ancienne_note not in notes[matiere]:
        raise ValueError("Cette note n'existe pas dans cette matière.")

    index = notes[matiere].index(ancienne_note)
    notes[matiere][index] = nouvelle_note
    sauvegarder()


def supprimer_matiere(matiere):
    if matiere not in notes:
        raise ValueError("Cette matière n'existe pas.")

    del notes[matiere]
    del coef[matiere]
    sauvegarder()


def supprimer_note(matiere, note):
    if matiere not in notes:
        raise ValueError("Cette matière n'existe pas.")

    if note not in notes[matiere]:
        raise ValueError("Cette note n'existe pas dans cette matière.")

    notes[matiere].remove(note)
    sauvegarder()


def calculer_moyennes():
    resultats = {}
    somme_ponderee = 0
    somme_coef = 0

    for matiere, liste_notes in notes.items():
        moyenne = calculer_moyenne(liste_notes)
        resultats[matiere] = moyenne
        somme_ponderee += moyenne * coef[matiere]
        somme_coef += coef[matiere]

    moyenne_generale = (
        somme_ponderee / somme_coef
        if somme_coef > 0
        else 0
    )

    return resultats, moyenne_generale


# Fonctions de l'ancienne interface terminal.
# Elles utilisent maintenant les fonctions métier ci-dessus.


def ajouter_notes():
    while True:
        matiere = input("\nMatiere (ou fin pour terminer) :")
        if matiere.lower() == "fin":
            break

        if matiere in notes:
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
            print(f"  {note}/20")


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

        if matiere in notes:
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

        if matiere not in notes:
            print(f"{matiere} n'existe pas")
            continue

        while True:
            try:
                supp = float(
                    input(f"Quelle note de {matiere} veux-tu supprimer ? ")
                )
            except ValueError:
                print("Veuillez entrer un nombre valide.")
                continue

            try:
                supprimer_note(matiere, supp)
                print(f"{supp} is removed")
                voir_notes()
                break
            except ValueError as erreur:
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
                ancienne_note = float(input("Ancienne note : "))
                nouvelle_note = float(input("Nouvelle note : "))
                modifier_note(matiere, ancienne_note, nouvelle_note)
                print(f"Note modifiee : {ancienne_note} -> {nouvelle_note}")
            except (TypeError, ValueError) as erreur:
                print(erreur)
        elif choix2 == "4":
            break
        else:
            print("Choix invalide")
