"""
Interface en ligne de commande : boucle interactive de type chat.

Usage : python -m src.cli
"""

from src.rag_chain import ask


def main() -> None:
    print("=== RAG sur mes notes — tape 'exit' pour quitter ===\n")
    while True:
        question = input("Toi > ").strip()
        if question.lower() in {"exit", "quit"}:
            print("A bientôt !")
            break
        if not question:
            continue

        try:
            result = ask(question)
        except FileNotFoundError as e:
            print(f"\n[Erreur] {e}\n")
            continue
        except EnvironmentError as e:
            print(f"\n[Erreur config] {e}\n")
            continue

        print(f"\nAssistant > {result['answer']}")
        if result["sources"]:
            print(f"(Sources : {', '.join(result['sources'])})\n")
        else:
            print()


if __name__ == "__main__":
    main()
