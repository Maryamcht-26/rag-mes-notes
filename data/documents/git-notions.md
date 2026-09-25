# Notes personnelles — Git

## merge ou rebase ?
git merge réunit deux branches en créant un commit de fusion, et conserve
l'historique réel. git rebase rejoue les commits d'une branche au-dessus
d'une autre, pour obtenir un historique linéaire plus lisible. Règle
importante : ne jamais faire de rebase sur une branche déjà partagée avec
d'autres développeurs, car cela réécrit l'historique.

## Annuler des changements
git restore fichier annule les modifications non indexées d'un fichier.
git reset --soft HEAD~1 annule le dernier commit mais garde les
modifications prêtes à être recommitées. git revert crée un nouveau commit
qui annule un commit précédent, sans réécrire l'historique : c'est la
méthode sûre sur une branche partagée.

## Le fichier .gitignore
Le .gitignore liste les fichiers que Git ne doit jamais suivre : secrets
(.env), dépendances (node_modules, venv), fichiers générés (build,
__pycache__). Un secret déjà commité reste dans l'historique même après
l'avoir ajouté au .gitignore : il faut alors révoquer la clé.

## Convention de messages de commit
Les Conventional Commits préfixent chaque message par un type : feat pour
une nouvelle fonctionnalité, fix pour une correction, docs, test, refactor
ou chore. Exemple : "feat: ajout de la recherche hybride BM25".
