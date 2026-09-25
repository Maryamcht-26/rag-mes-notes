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

# --- Barre latérale : documents et réglages ---
with st.sidebar:
    st.header("Documents")
    documents = sorted(
        p.relative_to(config.DOCUMENTS_DIR).as_posix()
        for p in config.DOCUMENTS_DIR.rglob("*")
        if p.suffix.lower() in {".md", ".txt", ".pdf"}
    )
    st.caption(f"{len(documents)} fichier(s) dans data/documents/")
    st.markdown("\n".join(f"- `{name}`" for name in documents))

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
st.caption("Les réponses sont générées uniquement à partir de tes documents, avec leurs sources.")

if "messages" not in st.session_state:
    st.session_state.messages = []


def show_answer(message: dict) -> None:
    st.markdown(message["content"])
    if message.get("passages"):
        with st.expander(f"Sources : {', '.join(message['sources'])}"):
            for i, passage in enumerate(message["passages"], start=1):
                st.markdown(f"**{i}. {passage['source']}**")
                st.text(passage["content"])


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        show_answer(message) if message["role"] == "assistant" else st.markdown(message["content"])

if question := st.chat_input("Pose une question sur tes notes..."):
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
