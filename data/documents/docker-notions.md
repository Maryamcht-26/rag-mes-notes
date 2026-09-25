# Notes personnelles — Docker

## Image ou conteneur ?
Une image Docker est un modèle en lecture seule qui contient le système de
fichiers et la commande de démarrage d'une application. Un conteneur est
une instance en cours d'exécution d'une image : on peut lancer plusieurs
conteneurs à partir de la même image, chacun isolé des autres.

## Le Dockerfile
Le Dockerfile décrit comment construire une image, instruction par
instruction. FROM choisit l'image de base, COPY ajoute des fichiers, RUN
exécute une commande pendant la construction, et CMD définit la commande
lancée au démarrage du conteneur. Chaque instruction crée une couche
(layer) mise en cache : on copie donc requirements.txt et on installe les
dépendances AVANT de copier le code, pour ne pas tout réinstaller à chaque
modification du code.

## Volumes
Les données écrites dans un conteneur disparaissent quand il est
supprimé. Un volume (option -v) monte un dossier de la machine hôte dans
le conteneur pour conserver les données, par exemple la base d'une
application PostgreSQL.

## Docker Compose
docker compose permet de décrire plusieurs services (application, base de
données, cache Redis) dans un fichier docker-compose.yml et de tous les
lancer avec une seule commande : docker compose up -d. L'option -d lance
les conteneurs en arrière-plan (mode détaché).
