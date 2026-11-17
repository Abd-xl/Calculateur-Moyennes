# Calculateur-Moyennes — feuille de route

## État actuel

La branche `feature/local-first-storage` retire PostgreSQL de l'application web.
Le carnet web durable est enregistré dans le `localStorage` de chaque
navigateur. Flask sert les pages et utilise un cache mémoire temporaire pour
conserver le rendu Jinja et vérifier les versions.

## Transition local-first

- [x] Conserver l'interface et les règles métier existantes.
- [x] Remplacer la persistance SQL par un cache mémoire temporaire.
- [x] Faire du stockage local du navigateur la source de réhydratation du cache.
- [x] Conserver la sauvegarde JSON, l'import et la restauration d'une copie.
- [x] Conserver le tableau admin sous forme de page de statut désactivée.
- [x] Retirer les routes de consultation, suppression et export des visiteurs.
- [x] Retirer les modèles, extensions, migrations et commandes SQL de l'application.
- [ ] Exécuter la suite complète de tests dans CI.
- [ ] Vérifier le flux de synchronisation dans un vrai navigateur.
- [ ] Vérifier le démarrage Render avec un seul worker avant fusion.
- [ ] Confirmer la récupération des données locales existantes et les sauvegardes JSON avant de désactiver la base de production.

## Limites à conserver en tête

- Pas de synchronisation entre navigateurs ou appareils.
- Le cache mémoire peut être perdu à chaque redémarrage ; les données durables
  doivent rester dans `localStorage` ou dans un export JSON.
- Plusieurs workers Gunicorn ou plusieurs instances Render ne sont pas
  compatibles avec ce cache temporaire.
- Les notes conservées uniquement dans PostgreSQL ne seront pas récupérées
  automatiquement. Les copies locales ou exports JSON sont nécessaires.

## Contraintes de mise en service

Ne pas modifier la branche `web-app`, fusionner la branche ou changer le
déploiement Render sans une étape explicite de mise en service.
