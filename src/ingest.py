"""
Étape 1 et 2 du pipeline : charger les documents, puis les découper en chunks.

Analogie Spring : ce fichier joue le rôle d'un "mapper" / DTO builder qui
transforme des fichiers bruts en objets prêts à être persistés.
"""

from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from src import config


def load_documents() -> list[Document]:
    """
    Charge tous les fichiers .md, .txt et .pdf du dossier data/documents.

    Chaque fichier devient un objet Document LangChain, qui contient :
    - page_content : le texte brut
    - metadata     : des infos annexes (ici, le chemin du fichier source),
                      qu'on retrouvera plus tard pour CITER la source
                      dans la réponse générée.
    """
    if not any(config.DOCUMENTS_DIR.glob("**/*")):
        raise FileNotFoundError(
            f"Aucun document trouvé dans {config.DOCUMENTS_DIR}. "
            "Ajoute des fichiers .md, .txt ou .pdf avant de lancer l'indexation."
        )

    # DirectoryLoader parcourt le dossier récursivement et applique
    # TextLoader à chaque fichier correspondant au glob "**/*.md" ou "**/*.txt".
    # C'est l'équivalent d'un Files.walk() + lecture de fichier en Java,
    # mais LangChain gère déjà l'encodage, les erreurs, etc.
    # PyPDFLoader produit un Document par PAGE (metadata["page"]), ce qui
    # permet ensuite de citer "cours.pdf, p. 12" plutôt que juste le fichier.
    loaders_config = [
        ("**/*.md", TextLoader, {"encoding": "utf-8"}),
        ("**/*.txt", TextLoader, {"encoding": "utf-8"}),
        ("**/*.pdf", PyPDFLoader, {}),
    ]
    documents: list[Document] = []

    for glob_pattern, loader_cls, loader_kwargs in loaders_config:
        loader = DirectoryLoader(
            str(config.DOCUMENTS_DIR),
            glob=glob_pattern,
            loader_cls=loader_cls,
            loader_kwargs=loader_kwargs,
            show_progress=False,
        )
        documents.extend(loader.load())

    for doc in documents:
        normalize_metadata(doc)
    return documents


def normalize_metadata(doc: Document) -> None:
    """
    Rend la source lisible et portable : "cours/rag.pdf" plutôt que
    "D:\\Projets\\...\\data\\documents\\cours\\rag.pdf". Le chemin absolu
    dépend de la machine, il n'a rien à faire dans une citation (ni dans
    une base vectorielle qu'on voudrait copier sur un serveur).
    Les numéros de page PDF passent aussi de 0-based à 1-based.
    """
    source = Path(doc.metadata.get("source", "inconnue"))
    try:
        doc.metadata["source"] = source.relative_to(config.DOCUMENTS_DIR).as_posix()
    except ValueError:
        doc.metadata["source"] = source.name
    if "page" in doc.metadata:
        doc.metadata["page"] = int(doc.metadata["page"]) + 1


def split_documents(documents: list[Document]) -> list[Document]:
    """
    Découpe chaque document en chunks de taille CHUNK_SIZE, avec un
    chevauchement de CHUNK_OVERLAP caractères entre deux chunks voisins.

    RecursiveCharacterTextSplitter essaie de couper intelligemment :
    il tente d'abord de couper sur un paragraphe ("\n\n"), puis une phrase,
    puis un mot, plutôt que de trancher au milieu d'un mot au hasard.
    C'est plus malin qu'un simple texte[i:i+800].
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    return chunks


def load_and_split() -> list[Document]:
    """Point d'entrée pratique qui enchaîne chargement + découpage."""
    documents = load_documents()
    chunks = split_documents(documents)
    print(f"{len(documents)} document(s) chargé(s) -> {len(chunks)} chunk(s) générés.")
    return chunks
