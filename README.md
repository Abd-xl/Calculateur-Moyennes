# Calculateur de Moyennes

## Description
Le **Calculateur de Moyennes** est une application Python permettant de gérer des notes scolaires par matière, calculer les moyennes pondérées et afficher diverses informations liées aux résultats scolaires.

---

### Fonctionnalités
- Ajouter des notes et leurs coefficients.
- Calculer les moyennes par matière et la moyenne générale.
- Afficher les notes d'une matière.
- Modifier, supprimer des notes ou des matières.
- Sauvegarder les données dans un fichier (`notes.json`) pour une utilisation ultérieure.
- Réinitialiser toutes les données.

---

## Prérequis
- Python 3.x
- Bibliothèque JSON (intégrée par défaut en Python)

---

## Installation

1. Clonez le dépôt sur votre machine locale :
   ```sh
   git clone https://github.com/Abd-xl/Calculateur-Moyennes.git
   ```

2. Exécutez le fichier principal de l’application :
   ```sh
   python main.py
   ```

---

## Instructions

### Menu principal
- **1. Ajouter des notes :** Ajoutez des notes pour des matières spécifiques.
- **2. Voir les moyennes :** Affichez les moyennes par matière et la moyenne générale.
- **3. Voir les notes :** Listez les notes enregistrées par matière.
- **4. Réinitialiser :** Supprimez toutes les données enregistrées.
- **5. Modifier :** Supprimez ou modifiez des matières ou des notes spécifiques.
- **6. Quitter :** Terminez l'application.

### Fichier de sauvegarde
Les données des notes et des coefficients sont enregistrées automatiquement dans un fichier `notes.json` pour être récupérées lors du prochain démarrage. Le programme est capable de gérer les erreurs de fichier, y compris les fichiers JSON corrompus.

---

## Contributions
Toute contribution est la bienvenue ! Voici comment vous pouvez aider :
1. **Fork** le dépôt.
2. Créez une nouvelle branche :
   ```sh
   git checkout -b feature/nouvelle-fonctionnalité
   ```
3. Apportez vos modifications et poussez vos changements :
   ```sh
   git commit -m "Ajout d'une nouvelle fonctionnalité"
   git push origin feature/nouvelle-fonctionnalité
   ```
4. Ouvrez une **Pull Request**.

---

## Historique des versions

### [1.2.0] - 2026-06-11
- Réorganisation en plusieurs fichiers : `main.py`, `gestion_notes.py`, `sauvegarde.py`.
- Ajout de validations utilisateur robustes pour éviter les erreurs.
- Amélioration de la gestion des sauvegardes : réinitialisation et gestion des JSON corrompus.

### [1.1.0] - 2026-05-21
- Possibilité de modifier une note existante.

### [1.0.0] - 2026-05-20
- Ajout du menu modifier/supprimer.
- Possibilité de supprimer une matière.
- Fonction permettant de réinitialiser toutes les données.
- Sauvegarde des données dans un fichier JSON.
- Affichage des notes enregistrées.

### [0.1.0] - 2026-05-16
- Première version du calculateur de moyennes.
- Ajout des fonctionnalités de calcul de moyennes et de gestion des matières/notes.

---

## Auteurs
- **Abd-xl** : Créateur principal