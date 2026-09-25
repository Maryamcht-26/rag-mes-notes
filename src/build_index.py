"""
Script exécutable : lance l'indexation complète (charge, découpe, vectorise).

Usage : python -m src.build_index

C'est l'équivalent d'une migration de base de données (comme Flyway) :
on l'exécute explicitement, à la demande, pas à chaque démarrage de l'app.
"""

from src.ingest import load_and_split
from src.vector_store import build_vector_store


def main() -> None:
    chunks = load_and_split()
    build_vector_store(chunks)
    print("Indexation terminée. Tu peux maintenant poser des questions avec `python -m src.cli`.")


if __name__ == "__main__":
    main()
