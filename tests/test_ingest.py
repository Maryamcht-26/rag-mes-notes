"""
Test unitaire simple : vérifie que le chunking respecte bien la taille
configurée et qu'aucun chunk n'est vide. Lance avec : pytest tests/
"""

from langchain.schema import Document
from src.ingest import normalize_metadata, split_documents
from src import config


def test_split_documents_respects_chunk_size():
    long_text = "Ceci est une phrase de test. " * 200  # texte volontairement long
    doc = Document(page_content=long_text, metadata={"source": "test.txt"})

    chunks = split_documents([doc])

    assert len(chunks) > 1, "Un texte long devrait être découpé en plusieurs chunks"
    for chunk in chunks:
        assert len(chunk.page_content) <= config.CHUNK_SIZE + config.CHUNK_OVERLAP
        assert chunk.page_content.strip() != ""


def test_split_documents_preserves_metadata():
    doc = Document(page_content="Un texte court.", metadata={"source": "notes.md"})
    chunks = split_documents([doc])

    assert all(chunk.metadata.get("source") == "notes.md" for chunk in chunks)


def test_normalize_metadata_makes_source_relative_and_page_one_based():
    doc = Document(
        page_content="x",
        metadata={"source": str(config.DOCUMENTS_DIR / "cours" / "rag.pdf"), "page": 0},
    )
    normalize_metadata(doc)

    assert doc.metadata["source"] == "cours/rag.pdf"
    assert doc.metadata["page"] == 1
