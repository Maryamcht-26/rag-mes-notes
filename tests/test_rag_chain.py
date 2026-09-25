"""
Tests de la chaîne RAG SANS clé API ni réseau : le LLM et le retriever sont
remplacés par des faux (comme des mocks en Java). On vérifie la logique
de NOTRE code (assemblage du contexte, sources, passages), pas la qualité
du modèle — ça, c'est le rôle de src/evaluate.py.
"""

from langchain.schema import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from src.evaluate import is_refusal, rank_of_expected
from src.rag_chain import build_rag_chain, format_docs, format_source, tokenize

DOCS = [
    Document(page_content="Le chunking découpe les documents.", metadata={"source": "rag.md"}),
    Document(page_content="Un index accélère les recherches.", metadata={"source": "cours.pdf", "page": 3}),
    Document(page_content="Chevauchement de 10 à 20%.", metadata={"source": "rag.md"}),
]


def fake_retriever(docs):
    return RunnableLambda(lambda question: docs)


def test_chain_returns_answer_sources_and_passages():
    llm = FakeListChatModel(responses=["Réponse de test."])
    chain = build_rag_chain(retriever=fake_retriever(DOCS), llm=llm)

    result = chain.invoke("Qu'est-ce que le chunking ?")

    assert result["answer"] == "Réponse de test."
    assert result["sources"] == ["cours.pdf, p. 3", "rag.md"]  # triées, sans doublon
    assert len(result["passages"]) == 3
    assert result["passages"][1] == {"source": "cours.pdf, p. 3", "content": "Un index accélère les recherches."}


def test_prompt_contains_retrieved_context_and_question():
    seen_prompts = []

    def capture(prompt_value):
        seen_prompts.append(prompt_value.to_string())
        return "ok"

    chain = build_rag_chain(retriever=fake_retriever(DOCS[:1]), llm=RunnableLambda(capture))
    chain.invoke("Ma question ?")

    assert "Le chunking découpe les documents." in seen_prompts[0]
    assert "[Source: rag.md]" in seen_prompts[0]
    assert "Question : Ma question ?" in seen_prompts[0]


def test_format_source_adds_page_only_for_pdfs():
    assert format_source(DOCS[0]) == "rag.md"
    assert format_source(DOCS[1]) == "cours.pdf, p. 3"


def test_format_docs_labels_each_chunk():
    text = format_docs(DOCS[:2])
    assert text.startswith("[Source: rag.md]\nLe chunking")
    assert "[Source: cours.pdf, p. 3]" in text


def test_tokenize_keeps_annotations_and_drops_punctuation():
    assert tokenize("Le rôle de @Repository, en Spring.") == ["le", "rôle", "de", "@repository", "en", "spring"]


def test_rank_of_expected():
    assert rank_of_expected(DOCS, "Chevauchement") == 3
    assert rank_of_expected(DOCS, "introuvable") is None


def test_is_refusal():
    assert is_refusal("Je ne sais pas.")
    assert is_refusal("Cette information ne figure pas dans le contexte.")
    assert not is_refusal("La taille recommandée est de 500 à 1000 caractères.")
