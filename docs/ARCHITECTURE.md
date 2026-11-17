# Architecture web

## Architecture actuelle

```text
Navigateur
   ├── pages HTML rendues par Flask
   ├── localStorage (source durable du carnet)
   └── fichiers JSON (sauvegarde et transfert manuel)
          │
          ├── envoi de l'état au chargement
          ▼
Routes publiques Flask
   ├── services métier
   └── cache mémoire temporaire
       ├── rendu des pages Jinja
       └── contrôle de version des modifications
```

Le point d'entrée `app.py` expose toujours `app:app` pour Gunicorn. La fabrique
`calculateur.create_app()` initialise les routes, la protection CSRF et un
repository mémoire propre au processus Flask.

Les services métier `grades.py`, `gradebook.py` et `validation.py` restent
indépendants du stockage. Le repository mémoire ne conserve qu'une copie
temporaire, indexée par un identifiant de navigateur placé dans la session
Flask signée. Les templates existants continuent ainsi à être rendus côté
serveur sans que les données durables soient enregistrées sur le serveur.

## Source durable et récupération

Le format stable du carnet est :

```json
{
  "notes": {
    "Maths": [{"note": 15, "bareme": 20}]
  },
  "coef": {"Maths": 3}
}
```

- `localStorage` est la source durable du carnet web sur un navigateur donné.
- `static/local_storage.js` initialise ou réhydrate le cache mémoire depuis la
  copie locale.
- Les modifications réussies sont recopiées dans `localStorage`.
- Une sauvegarde JSON exporte la copie locale, la copie locale précédente et
  un instantané du cache temporaire.
- Un import JSON ou une restauration locale remplace le carnet courant après
  confirmation et validation.
- Les anciennes sauvegardes contenant les champs `local_storage`,
  `previous_local_backup` ou `server_state` restent reconnues.

Le cache est borné en nombre de profils. Un profil évincé peut être rechargé
depuis le navigateur. Le cache n'est pas durable : après un redémarrage de
Render, le navigateur recharge son carnet local lors de la prochaine visite.

## Limites opérationnelles

- Un navigateur possède son propre carnet. Il n'y a plus de compte utilisateur,
  de profil centralisé ni de synchronisation entre appareils.
- Une suppression des données du site, une perte de navigateur ou d'appareil
  peut faire perdre le carnet si aucune sauvegarde JSON n'existe.
- Le serveur doit utiliser **un worker Gunicorn**. Les workers ou instances
  multiples ne partagent pas leur mémoire et produiraient des états distincts.
- L'interface est rendue par Flask : elle nécessite une connexion au serveur.
  Le cache mémoire n'est pas une prise en charge du mode hors ligne.
- Le jeton de profil est contenu dans une session Flask signée, protégée par
  `SECRET_KEY`; il ne contient pas les notes.

## Administration

La page `/admin` est conservée comme page de statut et répond HTTP 503. Elle
indique que l'administration est non fonctionnelle. Les routes de connexion,
de consultation, de suppression et d'export des visiteurs ne sont plus
enregistrées. Aucun profil visiteur centralisé n'est collecté.

## Déploiement

- Dépendances web : Flask, Flask-WTF et Gunicorn.
- Démarrage conseillé : `gunicorn --workers 1 app:app`.
- `SECRET_KEY` est obligatoire sur Render pour signer les sessions.
- Aucune configuration `DATABASE_URL` n'est requise.
- PostgreSQL, SQLite applicatif, SQLAlchemy, Flask-Migrate, Alembic et les
  migrations ne font plus partie de l'application web.

Le dépôt conserve `notes.json` et son repository JSON pour l'ancienne
interface CLI. Cette sauvegarde terminal est indépendante du `localStorage`
utilisé par l'application web.
