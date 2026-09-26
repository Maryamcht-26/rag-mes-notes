## Retrieval — 32 questions, k=4

| Mode | Hit@1 | Hit@4 | MRR |
|---|---|---|---|
| dense | 50% | 59% | 0.54 |
| hybrid | 66% | 78% | 0.71 |

Passage non retrouvé en mode dense :
- Qu'arrive-t-il si les bons passages ne sont pas retrouvés ?
- Que signifie l'option -d ?
- Comment lister tous les clients même ceux sans commande ?
- Est-ce que je peux faire un rebase sur une branche partagée ?
- Comment annuler mon dernier commit en gardant mes modifications ?
- J'ai commité ma clé API par erreur, que faire ?
- Quelle commande démarre tous les services en arrière-plan ?
- Quelle est la plus petite unité qu'on peut déployer dans Kubernetes ?
- Quel composant choisit la machine sur laquelle un pod va tourner ?
- Quel est le type de Service utilisé si on n'en précise pas ?
- J'ai oublié un fichier dans mon dernier commit, comment le rajouter ?
- Comment ajouter un dépôt distant avec un nom court ?
- Comment créer une branche et basculer dessus en une seule commande ?

Passage non retrouvé en mode hybrid :
- Que signifie l'option -d ?
- Comment annuler mon dernier commit en gardant mes modifications ?
- J'ai commité ma clé API par erreur, que faire ?
- Quelle est la plus petite unité qu'on peut déployer dans Kubernetes ?
- Quel composant choisit la machine sur laquelle un pod va tourner ?
- J'ai oublié un fichier dans mon dernier commit, comment le rajouter ?
- Comment créer une branche et basculer dessus en une seule commande ?

## Génération — openai/gpt-oss-20b, mode hybrid

| Métrique | Score |
|---|---|
| Réponses données (questions dans le périmètre) | 94% |
| Refus corrects (questions hors périmètre) | 100% |

Refus à tort :
- Comment annuler mon dernier commit en gardant mes modifications ?
- Quel composant choisit la machine sur laquelle un pod va tourner ?
