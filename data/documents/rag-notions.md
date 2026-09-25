# Notes personnelles — RAG

## Qu'est-ce que le chunking ?
Le chunking consiste à découper un document long en morceaux plus petits
avant de les indexer. On utilise souvent une taille de 500 à 1000
caractères avec un chevauchement (overlap) de 10 à 20% pour éviter de
couper une idée importante entre deux chunks.

## Différence entre recherche dense et recherche sparse
La recherche sparse (comme BM25) compare les mots exacts entre la requête
et les documents, un peu comme une recherche par mots-clés. La recherche
dense utilise des embeddings pour comparer le sens des phrases, même si
les mots utilisés sont différents. Beaucoup de systèmes en production
combinent les deux approches (hybrid search) pour de meilleurs résultats.

## Pourquoi Chroma est un bon choix pour débuter
ChromaDB est une base de données vectorielle open-source, simple à
installer (pip install chromadb), qui peut tourner entièrement en local
sans serveur externe. C'est un excellent point de départ avant de passer
à une solution plus scalable comme Pinecone ou Weaviate en production.

## Limites du RAG
Un système RAG dépend entièrement de la qualité du retrieval. Si les
chunks pertinents ne sont pas retrouvés, le modèle peut quand même
générer une réponse qui semble plausible mais qui est en fait fausse,
car il ne "sait" pas qu'il lui manque une information.
