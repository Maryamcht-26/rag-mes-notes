# Notes personnelles — SQL

## INNER JOIN et LEFT JOIN
INNER JOIN ne garde que les lignes qui ont une correspondance dans les
deux tables. LEFT JOIN garde toutes les lignes de la table de gauche, et
remplit les colonnes de la table de droite avec NULL quand il n'y a pas
de correspondance. Exemple : lister tous les clients, même ceux qui n'ont
passé aucune commande, nécessite un LEFT JOIN.

## WHERE ou HAVING ?
WHERE filtre les lignes AVANT le regroupement, HAVING filtre les groupes
APRÈS un GROUP BY. On ne peut pas utiliser une fonction d'agrégation comme
COUNT ou SUM dans un WHERE : pour garder les clients ayant plus de 5
commandes, on écrit GROUP BY client_id HAVING COUNT(*) > 5.

## Les index
Un index accélère les recherches sur une colonne, comme l'index à la fin
d'un livre, mais il ralentit les insertions et les mises à jour car il
doit être maintenu. On indexe les colonnes souvent utilisées dans les
WHERE et les jointures, pas toutes les colonnes.

## Transactions et propriétés ACID
Une transaction regroupe plusieurs opérations qui réussissent ou échouent
ensemble. ACID signifie Atomicité, Cohérence, Isolation et Durabilité.
En Spring, l'annotation @Transactional ouvre une transaction autour d'une
méthode et fait un rollback automatique si une exception non vérifiée
(RuntimeException) est levée.
