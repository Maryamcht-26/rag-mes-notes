"""
Évaluation chiffrée du système RAG, sur le jeu de questions eval/questions.json.

Usage :
    python -m src.evaluate          # retrieval seul : gratuit, sans clé API
    python -m src.evaluate --llm    # + qualité des réponses (appelle le LLM)

Pourquoi ce script ? "Ça a l'air de marcher" ne suffit pas : pour savoir si
un changement (taille de chunk, modèle d'embeddings, recherche hybride...)
améliore vraiment le système, il faut une mesure reproductible — l'équivalent
des tests de non-régression, mais pour la qualité des résultats.

Métriques de retrieval (une question = un passage attendu) :
- Hit@1 : le bon passage est-il classé PREMIER ?
- Hit@k : le bon passage est-il parmi les k envoyés au LLM ?
          (s'il n'y est pas, le LLM ne peut PAS bien répondre)
- MRR   : Mean Reciprocal Rank, moyenne de 1/rang du bon passage
          (1.0 = toujours premier, 0.5 = en moyenne deuxième...)

Métriques de génération (--llm) :
- Réponses données : questions dans le périmètre où le LLM répond
  (au lieu de dire à tort qu'il ne sait pas)
- Refus corrects : questions HORS périmètre où le LLM dit qu'il ne sait
  pas (au lieu d'inventer = halluciner)
"""

import argparse
import json
import time

from src import config
from src.rag_chain import build_rag_chain, build_retriever
from src.vector_store import get_vector_store

QUESTIONS_FILE = config.BASE_DIR / "eval" / "questions.json"
RESULTS_FILE = config.BASE_DIR / "eval" / "results.md"

REFUSAL_MARKERS = ("ne sais pas", "pas dans le contexte", "ne figure pas", "pas mentionné", "aucune information")


def rank_of_expected(docs, expected: str) -> int | None:
    """Rang (1-based) du premier chunk contenant le passage attendu, ou None."""
    for rank, doc in enumerate(docs, start=1):
        if expected in doc.page_content:
            return rank
    return None


def evaluate_retrieval(retriever, questions: list[dict]) -> dict:
    ranks = [rank_of_expected(retriever.invoke(q["question"]), q["expected"]) for q in questions]
    n = len(ranks)
    return {
        "hit@1": sum(r == 1 for r in ranks) / n,
        f"hit@{config.TOP_K}": sum(r is not None for r in ranks) / n,
        "mrr": sum(1 / r for r in ranks if r) / n,
        "misses": [q["question"] for q, r in zip(questions, ranks) if r is None],
    }


def is_refusal(answer: str) -> bool:
    answer = answer.lower().replace("’", "'")
    return any(marker in answer for marker in REFUSAL_MARKERS)


def evaluate_generation(chain, in_scope: list[dict], out_of_scope: list[str]) -> dict:
    def answer(question: str) -> str:
        time.sleep(2)  # reste sous la limite de requêtes/minute du tier gratuit Groq
        return chain.invoke(question)["answer"]

    answered = [not is_refusal(answer(q["question"])) for q in in_scope]
    refused = [is_refusal(answer(q)) for q in out_of_scope]
    return {
        "answered": sum(answered) / len(answered),
        "refused": sum(refused) / len(refused),
        "wrongly_refused": [q["question"] for q, ok in zip(in_scope, answered) if not ok],
        "hallucinated": [q for q, ok in zip(out_of_scope, refused) if not ok],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue le retrieval (et optionnellement les réponses).")
    parser.add_argument("--llm", action="store_true", help="évalue aussi les réponses du LLM (utilise l'API)")
    args = parser.parse_args()

    data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    vector_store = get_vector_store()
    k = config.TOP_K

    lines = [
        f"## Retrieval — {len(data['in_scope'])} questions, k={k}\n",
        f"| Mode | Hit@1 | Hit@{k} | MRR |",
        "|---|---|---|---|",
    ]
    all_misses = {}
    for mode in ("dense", "hybrid"):
        scores = evaluate_retrieval(build_retriever(vector_store, mode=mode), data["in_scope"])
        lines.append(f"| {mode} | {scores['hit@1']:.0%} | {scores[f'hit@{k}']:.0%} | {scores['mrr']:.2f} |")
        all_misses[mode] = scores["misses"]

    for mode, misses in all_misses.items():
        if misses:
            lines.append(f"\nPassage non retrouvé en mode {mode} :")
            lines.extend(f"- {q}" for q in misses)

    if args.llm:
        chain = build_rag_chain(retriever=build_retriever(vector_store))
        gen = evaluate_generation(chain, data["in_scope"], data["out_of_scope"])
        lines += [
            f"\n## Génération — {config.LLM_MODEL_NAME}, mode {config.RETRIEVAL_MODE}\n",
            "| Métrique | Score |",
            "|---|---|",
            f"| Réponses données (questions dans le périmètre) | {gen['answered']:.0%} |",
            f"| Refus corrects (questions hors périmètre) | {gen['refused']:.0%} |",
        ]
        if gen["wrongly_refused"]:
            lines.append("\nRefus à tort :")
            lines.extend(f"- {q}" for q in gen["wrongly_refused"])
        if gen["hallucinated"]:
            lines.append("\nRéponse inventée hors périmètre :")
            lines.extend(f"- {q}" for q in gen["hallucinated"])

    report = "\n".join(lines)
    print(report)
    RESULTS_FILE.write_text(report + "\n", encoding="utf-8")
    print(f"\nRésultats enregistrés dans {RESULTS_FILE.relative_to(config.BASE_DIR)}")


if __name__ == "__main__":
    main()
