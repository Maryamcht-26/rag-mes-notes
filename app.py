"""
Interface web Streamlit : chat avec historique, passages sources affichés
sous chaque réponse, et ajout de documents + ré-indexation depuis la page.

Usage : streamlit run app.py

Rappel Streamlit : tout le fichier est ré-exécuté de haut en bas à chaque
interaction. Ce qui doit survivre entre deux exécutions (l'historique du
chat) vit dans st.session_state.
"""

import streamlit as st

from src import config
from src.ingest import load_and_split
from src.rag_chain import ask, reset_chain
from src.vector_store import build_vector_store

st.set_page_config(page_title="RAG sur mes notes", page_icon="🔎")

EXAMPLES = [
    "Quelle est la différence entre INNER JOIN et LEFT JOIN ?",
    "Comment revenir à la version précédente d'un déploiement Kubernetes ?",
    "Quelle est la différence entre merge et rebase ?",
]


@st.cache_resource(show_spinner="Première ouverture : indexation des documents (environ 1 minute)...")
def ensure_index() -> None:
    """
    Sur un serveur neuf (Streamlit Cloud, conteneur Docker), la base
    vectorielle n'existe pas encore : data/vector_db/ n'est pas versionné.
    cache_resource garantit que l'indexation ne tourne qu'une fois par
    processus, même si plusieurs visiteurs arrivent en même temps.
    """
    if not config.VECTOR_DB_DIR.exists():
        build_vector_store(load_and_split())


ensure_index()

# --- Barre latérale : documents et réglages ---
with st.sidebar:
    st.header("Documents")
    documents = sorted(
        p.relative_to(config.DOCUMENTS_DIR).as_posix()
        for p in config.DOCUMENTS_DIR.rglob("*")
        if p.suffix.lower() in {".md", ".txt", ".pdf"}
    )
    with st.expander(f"{len(documents)} fichier(s) indexé(s)"):
        st.markdown("\n".join(f"- `{name}`" for name in documents))

    if config.DEMO_MODE:
        st.caption("Démo publique : l'ajout de documents est désactivé. Clone le projet pour indexer les tiens.")
    else:
        uploaded = st.file_uploader("Ajouter des documents", type=["md", "txt", "pdf"], accept_multiple_files=True)
        if st.button("Indexer", disabled=not uploaded, use_container_width=True):
            for file in uploaded:
                (config.DOCUMENTS_DIR / file.name).write_bytes(file.getvalue())
            with st.spinner("Découpage et calcul des embeddings..."):
                build_vector_store(load_and_split())
                reset_chain()  # la chaîne en cache pointait sur l'ancien index
            st.success(f"{len(uploaded)} document(s) ajouté(s) et indexé(s).")
            st.rerun()

    st.header("Réglages")
    st.markdown(
        f"- Recherche : **{config.RETRIEVAL_MODE}**, top {config.TOP_K}\n"
        f"- LLM : `{config.LLM_MODEL_NAME}` ({config.LLM_PROVIDER})"
    )
    if st.button("Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# --- Zone de chat ---
st.title("🔎 RAG sur mes notes")
st.caption(
    "Les réponses sont générées uniquement à partir des documents indexés "
    "(notes DevOps, documentation Kubernetes, livre Pro Git), avec leurs sources."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("**Exemples de questions :**\n" + "\n".join(f"- {q}" for q in EXAMPLES))


def show_answer(message: dict) -> None:
    st.markdown(message["content"])
    if message.get("passages"):
        with st.expander(f"Sources : {', '.join(message['sources'])}"):
            for i, passage in enumerate(message["passages"], start=1):
                st.markdown(f"**{i}. {passage['source']}**")
                st.text(passage["content"])


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Un if/else classique, pas une expression ternaire : Streamlit affiche
        # automatiquement la valeur de toute expression seule sur sa ligne
        # ("magic"), ce qui faisait planter la page dès la 2e question.
        if message["role"] == "assistant":
            show_answer(message)
        else:
            st.markdown(message["content"])

asked = sum(m["role"] == "user" for m in st.session_state.messages)
limit_reached = config.DEMO_MODE and asked >= config.DEMO_MAX_QUESTIONS
if limit_reached:
    st.info(f"Limite de {config.DEMO_MAX_QUESTIONS} questions atteinte pour cette démo publique.")

if question := st.chat_input("Pose une question sur tes notes...", disabled=limit_reached):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche des passages et génération de la réponse..."):
            try:
                result = ask(question)
            except (FileNotFoundError, EnvironmentError) as e:
                st.error(str(e))
                st.stop()
        message = {"role": "assistant", "content": result["answer"], **result}
        show_answer(message)
    st.session_state.messages.append(message)
