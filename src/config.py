"""
Configuration centralisée du projet.

Toutes les valeurs "réglables" (chemins, tailles de chunks, modèles...)
vivent ici plutôt que d'être éparpillées dans le code.
C'est l'équivalent d'un application.yml / application.properties en Spring :
un seul endroit à modifier pour changer le comportement de l'app.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Charge les variables du fichier .env dans l'environnement (comme un .env
# lu par Spring Boot via spring-dotenv, ou un application-local.yml non versionné).
load_dotenv()

# --- Chemins ---
BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"

# --- Chunking ---
# Taille d'un chunk en caractères, et chevauchement entre deux chunks
# consécutifs pour ne pas couper une idée en deux.
# 500 et non 800 (V1.3) : le modèle d'embeddings ignore tout ce qui dépasse
# ~100 mots (vérifié : deux textes identiques sur 100 mots puis différents
# donnent le même vecteur). Un chunk de 800 caractères (~130 mots) avait
# donc sa fin invisible pour la recherche sémantique. Mesuré sur 32
# questions et 17 documents : Hit@1 47% -> 62%, MRR 0.57 -> 0.68.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 75

# --- Embeddings ---
# Modèle open-source, léger, tourne en local (CPU) sans clé API, via
# FastEmbed (ONNX runtime) — pas besoin d'installer PyTorch.
# Version "paraphrase-multilingual" car nos notes sont en français : un
# modèle anglais uniquement (ex. all-MiniLM-L6-v2) donnerait de moins
# bons résultats de similarité sur du texte français.
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# --- Retrieval ---
# Nombre de chunks les plus proches à récupérer pour chaque question.
TOP_K = 4

# "dense"  : recherche sémantique seule (embeddings)
# "hybrid" : sémantique + mots-clés (BM25), fusionnés par EnsembleRetriever.
# L'hybride retrouve mieux les termes exacts (noms propres, annotations
# comme @Transactional, commandes...) que les embeddings seuls ont tendance
# à "lisser". Voir evaluate.py pour la comparaison chiffrée des deux modes.
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "hybrid")
# Poids de chaque recherche dans la fusion hybride (dense, BM25).
HYBRID_WEIGHTS = (0.5, 0.5)
# Nombre de candidats renvoyés par CHAQUE recherche avant la fusion hybride.
HYBRID_CANDIDATES = 20

# --- LLM de génération ---
# On garde le fournisseur interchangeable : "groq" (gratuit, rapide, par
# défaut) ou "openai". Le reste du code ne connaît que get_llm() dans
# rag_chain.py, jamais directement "GroqClient" ou "OpenAIClient" —
# c'est le même principe qu'une interface Java injectée par Spring plutôt
# qu'une classe concrète en dur.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "openai/gpt-oss-20b")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Démo publique (Streamlit Community Cloud) ---
# DEMO_MODE=true masque l'ajout de documents (sur un serveur partagé, un
# fichier envoyé par un visiteur serait visible par tous les autres) et
# limite le nombre de questions par visiteur, pour ne pas épuiser le quota
# gratuit de la clé Groq.
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
DEMO_MAX_QUESTIONS = int(os.getenv("DEMO_MAX_QUESTIONS", "15"))

# Nom de la "collection" dans la base vectorielle (comme le nom d'une table).
COLLECTION_NAME = "mes_notes"
