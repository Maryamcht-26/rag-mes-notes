"""
Étapes 4 et 5 du pipeline : retrieval (recherche de similarité) puis
génération augmentée par le contexte trouvé.

Analogie Spring : get_llm() est comme un @Bean choisi selon un profil actif
(application-dev vs application-prod) : le reste du code appelle juste
"le LLM" sans savoir s'il parle à Groq ou OpenAI.
"""

import re
from functools import lru_cache

from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda

from src import config
from src.vector_store import get_all_chunks, get_vector_store

# Le prompt "système" qui encadre le LLM : on lui dit explicitement de ne
# répondre qu'à partir du contexte fourni, pour limiter les hallucinations.
# C'est LA différence entre "un chatbot qui invente" et "un chatbot RAG fiable".
PROMPT_TEMPLATE = """Tu es un assistant qui répond aux questions UNIQUEMENT à partir
du contexte ci-dessous, extrait des notes de l'utilisateur.

Règles :
- Si la réponse n'est pas dans le contexte, dis clairement que tu ne sais pas.
- Ne réponds jamais en te basant sur des connaissances externes.
- Cite les passages pertinents quand c'est utile.
- Réponds en français, de façon concise et précise.

Contexte :
{context}

Question : {question}

Réponse :"""


def get_llm():
    """
    Retourne le client LLM selon la variable d'environnement LLM_PROVIDER.
    Groq est utilisé par défaut car son offre gratuite est généreuse et
    rapide, ce qui est idéal pour un projet perso / une démo d'entretien.
    """
    if config.LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq

        if not config.GROQ_API_KEY:
            raise EnvironmentError(
                "GROQ_API_KEY manquant. Crée une clé gratuite sur console.groq.com "
                "et ajoute-la dans ton fichier .env."
            )
        return ChatGroq(model=config.LLM_MODEL_NAME, api_key=config.GROQ_API_KEY, temperature=0)

    if config.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        if not config.OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY manquant dans le fichier .env.")
        return ChatOpenAI(model=config.LLM_MODEL_NAME, api_key=config.OPENAI_API_KEY, temperature=0)

    raise ValueError(f"LLM_PROVIDER inconnu : {config.LLM_PROVIDER!r} (attendu: 'groq' ou 'openai')")


def tokenize(text: str) -> list[str]:
    """
    Découpage en mots pour BM25. Le découpage par défaut (text.split())
    laisse la ponctuation collée ("chunks," != "chunks") et respecte la
    casse ; on passe en minuscules et on garde le "@" pour que les
    annotations Java (@Repository) restent des mots-clés exacts.
    """
    return re.findall(r"[@\w]+", text.lower())


def build_retriever(
    vector_store,
    mode: str = config.RETRIEVAL_MODE,
    k: int = config.TOP_K,
    candidates: int = config.HYBRID_CANDIDATES,
):
    """
    Construit le retriever selon le mode :
    - "dense"  : similarité d'embeddings seule (sens de la phrase)
    - "hybrid" : dense + BM25 (mots exacts), fusionnés par EnsembleRetriever
                 avec la Reciprocal Rank Fusion : un chunk bien classé par
                 les deux recherches remonte en tête.

    En hybride, chaque recherche renvoie `candidates` chunks AVANT la fusion
    (et non k) : un passage classé 6e par le dense mais 1er par BM25 doit
    pouvoir gagner la fusion. Avec seulement k candidats de chaque côté, il
    était éliminé avant même d'être comparé.

    Retourne un Runnable : question (str) -> liste de k Documents.
    """
    if mode == "dense":
        return vector_store.as_retriever(search_kwargs={"k": k})
    if mode != "hybrid":
        raise ValueError(f"RETRIEVAL_MODE inconnu : {mode!r} (attendu: 'dense' ou 'hybrid')")

    dense = vector_store.as_retriever(search_kwargs={"k": candidates})
    bm25 = BM25Retriever.from_documents(get_all_chunks(vector_store), preprocess_func=tokenize, k=candidates)
    ensemble = EnsembleRetriever(retrievers=[dense, bm25], weights=list(config.HYBRID_WEIGHTS))
    # La fusion peut renvoyer jusqu'à 2*k chunks distincts : on garde les k meilleurs
    # pour que le prompt ait la même taille quel que soit le mode.
    return ensemble | RunnableLambda(lambda docs: docs[:k])


def format_source(doc) -> str:
    """'cours.pdf, p. 3' pour un PDF, 'notes.md' sinon."""
    source = doc.metadata.get("source", "inconnue")
    page = doc.metadata.get("page")
    return f"{source}, p. {page}" if page else source


def format_docs(docs) -> str:
    """
    Assemble les chunks retrouvés en un seul bloc de texte, avec leur
    source, pour les injecter dans {context} du prompt.
    """
    return "\n\n".join(f"[Source: {format_source(doc)}]\n{doc.page_content}" for doc in docs)


def build_rag_chain(retriever=None, llm=None):
    """
    Construit la chaîne complète : question -> retrieval (UNE seule fois)
    -> prompt -> LLM -> {réponse, sources, passages}.

    retriever et llm sont injectables (par défaut : la vraie base et le vrai
    LLM). Les tests passent un faux LLM et un faux retriever : ils tournent
    sans clé API, sans réseau, et en quelques millisecondes — comme un
    @MockBean en Spring.

    Correctif V1.1 : RunnableParallel exécute le retrieval une seule fois et
    partage son résultat (`docs`) entre le contexte du prompt et les sources.

    La syntaxe "|" vient de LCEL (LangChain Expression Language) : chaque
    étape prend la sortie de la précédente en entrée, un peu comme un
    pipeline de flux Java (Stream.map().filter()...).
    """
    retriever = retriever or build_retriever(get_vector_store())
    llm = llm or get_llm()

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    generation = prompt | llm | StrOutputParser()

    def generate_and_collect_sources(inputs: dict) -> dict:
        """
        Reçoit {"docs": [...], "question": "..."} et produit la réponse,
        la liste des sources (sans doublons) et les passages utilisés
        (affichés dans l'interface pour que l'utilisateur puisse vérifier).
        """
        docs = inputs["docs"]
        answer = generation.invoke({"context": format_docs(docs), "question": inputs["question"]})
        sources = sorted({format_source(doc) for doc in docs})
        passages = [{"source": format_source(doc), "content": doc.page_content} for doc in docs]
        return {"answer": answer, "sources": sources, "passages": passages}

    return (
        RunnableParallel(docs=retriever, question=RunnablePassthrough())
        | RunnableLambda(generate_and_collect_sources)
    )


@lru_cache(maxsize=1)
def get_chain():
    """
    Construit la chaîne une seule fois puis la réutilise (V1.2). Avant, chaque
    question rechargeait le modèle d'embeddings, rouvrait Chroma et recréait
    le client LLM. Après une ré-indexation, appeler reset_chain().
    """
    return build_rag_chain()


def reset_chain() -> None:
    """Oublie la chaîne en cache (à appeler après build_index)."""
    get_chain.cache_clear()


def ask(question: str) -> dict:
    """
    Point d'entrée simple : pose une question, récupère la réponse, les
    sources et les passages utilisés, en un seul passage dans la base.
    """
    return get_chain().invoke(question)
