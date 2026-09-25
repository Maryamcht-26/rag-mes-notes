"""
Étape 3 du pipeline : créer/charger la base vectorielle (Chroma).

Analogie Spring/JPA : ce fichier joue le rôle d'un Repository. On ne
manipule jamais Chroma directement ailleurs dans le projet — tout passe
par get_vector_store() ou build_vector_store(), comme on passerait
toujours par un @Repository plutôt que par le driver JDBC en direct.
"""

from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.schema import Document

from src import config

# Désactive la télémétrie anonyme de Chroma. Sans ça, la première
# indexation affiche des warnings inoffensifs ("Failed to send telemetry
# event...") qui n'ont aucun impact mais peuvent inquiéter inutilement
# quelqu'un qui découvre le projet.
#
# ATTENTION (piège vérifié en pratique) : dès qu'on fournit un objet
# client_settings à Chroma, il FAUT explicitement passer is_persistent=True.
# Sans ce flag, langchain_chroma bascule silencieusement en mode mémoire
# (rien n'est écrit sur disque, même si persist_directory est indiqué par
# ailleurs) — un bug facile à ne jamais remarquer tant qu'on ne redémarre
# pas le processus entre l'indexation et les questions.
_CHROMA_SETTINGS = Settings(anonymized_telemetry=False, is_persistent=True)


def get_embeddings() -> FastEmbedEmbeddings:
    """
    Instancie le modèle d'embeddings. FastEmbed fait tourner un petit
    modèle ONNX en local (CPU) : pas de clé API, pas de coût, et surtout
    pas besoin d'installer PyTorch (plusieurs Go) comme le ferait
    sentence-transformers — un plus pour un projet qu'on veut pouvoir
    cloner et lancer rapidement sur une machine perso ou en CI.
    """
    return FastEmbedEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)


def build_vector_store(chunks: list[Document]) -> Chroma:
    """
    Crée (ou écrase) la base vectorielle à partir d'une liste de chunks.
    C'est l'étape d'INDEXATION : à lancer une fois, puis à chaque fois
    que les documents source changent.

    Chroma.from_documents fait deux choses pour chaque chunk :
    1. calcule son embedding via le modèle fourni
    2. le stocke sur disque avec son texte et ses métadonnées

    Correctif V1.2 : Chroma.from_documents AJOUTE à une collection
    existante, il ne la remplace pas. Sans la suppression ci-dessous,
    chaque ré-indexation dupliquait tous les chunks (vérifié : 5 + 12 = 17
    chunks en base après une 2e indexation), et le retrieval renvoyait
    plusieurs fois le même passage.
    """
    if config.VECTOR_DB_DIR.exists():
        get_vector_store().delete_collection()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.VECTOR_DB_DIR),
        client_settings=_CHROMA_SETTINGS,
    )
    print(f"Base vectorielle créée avec {len(chunks)} chunks -> {config.VECTOR_DB_DIR}")
    return vector_store


def get_vector_store() -> Chroma:
    """
    Recharge une base vectorielle déjà indexée sur disque, sans tout
    recalculer. C'est ce qu'on utilise à chaque question posée par
    l'utilisateur (étape de RETRIEVAL).
    """
    if not config.VECTOR_DB_DIR.exists():
        raise FileNotFoundError(
            f"Aucune base vectorielle trouvée dans {config.VECTOR_DB_DIR}. "
            "Lance d'abord `python -m src.build_index` pour indexer tes documents."
        )
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(config.VECTOR_DB_DIR),
        client_settings=_CHROMA_SETTINGS,
    )


def get_all_chunks(vector_store: Chroma) -> list[Document]:
    """
    Relit tous les chunks stockés (texte + métadonnées), sans leurs vecteurs.
    Utilisé par la recherche BM25, qui travaille sur le texte brut et a
    besoin de tout le corpus en mémoire. Relire depuis Chroma (plutôt que
    re-découper les fichiers) garantit que BM25 et la recherche dense
    voient exactement les mêmes chunks.
    """
    data = vector_store.get(include=["documents", "metadatas"])
    return [
        Document(page_content=text, metadata=metadata or {})
        for text, metadata in zip(data["documents"], data["metadatas"])
    ]
