# Notes personnelles — Spring Boot

## Le rôle de l'annotation @Repository
@Repository marque une classe comme couche d'accès aux données. Spring
traduit automatiquement les exceptions bas niveau (JDBC, Hibernate) en
exceptions Spring génériques (DataAccessException), ce qui découple le
code métier de la technologie de persistance utilisée.

## Différence entre @Component, @Service et @Repository
Les trois annotations enregistrent une classe comme bean Spring, mais
elles ont un rôle sémantique différent : @Component est générique,
@Service marque la couche métier, @Repository marque la couche de
persistance. Fonctionnellement elles sont presque identiques, mais elles
aident à la lisibilité du code et activent des comportements spécifiques
(comme la traduction d'exceptions pour @Repository).

## Qu'est-ce que l'injection de dépendances ?
L'injection de dépendances est un principe où un objet ne crée pas
lui-même ses dépendances, mais les reçoit de l'extérieur (par le
constructeur, un setter, ou un champ). Spring gère ce câblage
automatiquement via son conteneur IoC (Inversion of Control), ce qui
facilite les tests unitaires en permettant d'injecter des mocks.

## Profils Spring (application-dev.yml, application-prod.yml)
Les profils permettent d'avoir des configurations différentes selon
l'environnement d'exécution. On active un profil avec la propriété
spring.profiles.active, et Spring charge automatiquement le fichier de
configuration correspondant.
