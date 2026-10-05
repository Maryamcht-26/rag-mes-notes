"""
Évaluation de la QUALITÉ des réponses avec RAGAS, en complément de
evaluate.py (qui mesure le retrieval : Hit@k, MRR).

Usage :
    pip install -r requirements-eval.txt   # dépendances RAGAS (pas dans requirements-dev.txt)
    python -m src.evaluate_ragas           # 8 questions par défaut
    python -m src.evaluate_ragas --sample 32

Pourquoi en plus de evaluate.py ?
Hit@k et MRR répondent à "a-t-on trouvé le bon passage ?", pas à "la
réponse générée est-elle fidèle à ce passage ?". Un retrieval parfait
n'empêche pas le LLM d'ajouter un détail inventé. RAGAS fait juger chaque
réponse par un second LLM, sur la métrique **Faithfulness** (fidélité) :
le LLM-juge découpe la réponse en affirmations, puis vérifie chacune
contre les passages retrouvés. Score = part d'affirmations soutenues par
le contexte (1.0 = aucune invention). Ne demande PAS de réponse de
référence écrite à la main (juste question + réponse + passages).

Le LLM-juge est le même que celui de l'app (get_llm(), Groq par défaut) :
pas de clé OpenAI nécessaire. Comme RAGAS déclenche PLUSIEURS appels LLM
par question (en plus de la génération de la réponse elle-même), le tier
gratuit Groq est vite sollicité : requêtes sérialisées (max_workers=1,
RAGAS réessaie automatiquement en cas de 429) et échantillon limité par
défaut. max_tokens=8192 sur le LLM-juge : "openai/gpt-oss-20b" raisonne
"en interne" avant de répondre, et ce raisonnement consomme des tokens —
avec la limite par défaut (~réponses courtes de l'app), le JSON attendu
par RAGAS était tronqué avant la fin (LLMDidNotFinishException). Même à
8192, certaines questions échouent encore de façon reproductible (à
temperature=0, le LLM "réfléchit" toujours aussi longtemps sur une même
question/réponse : si son raisonnement dépasse la limite pour l'une
d'elles, il la dépassera à chaque run) : RAGAS renvoie alors `nan` pour
CETTE question plutôt que de planter tout le run, et la moyenne affichée
ignore les `nan` — c'est un comportement attendu et déjà vérifié
(constaté systématiquement sur la même question dans nos tests), pas un
bug à corriger question par question. Piste si ça devient gênant :
augmenter encore max_tokens, ou exclure cette question du jeu RAGAS.

Volontairement PAS branché sur la CI pour l'instant : il faudrait une clé
API en secret GitHub (la CI actuelle n'en a besoin d'aucune, cf. README)
et ça ralentirait chaque push de plusieurs minutes. À lancer en local, à
la main, après un changement du prompt ou du retrieval.

Note : la métrique **Answer Relevancy** (pertinence : la réponse adresse-
t-elle vraiment la question posée, et pas une question voisine ?) n'est
volontairement PAS incluse. Elle a besoin d'un modèle d'embeddings, et le
wrapper RAGAS 0.4.3 pour les embeddings LangChain (`LangchainEmbeddingsWrapper`)
plante avec `FastEmbedEmbeddings` (celui du projet) : erreur Pydantic
`EmbeddingUsageEvent.model` qui reçoit l'objet modèle chargé au lieu d'un
nom de modèle (chaîne) — un bug de compatibilité RAGAS/FastEmbed, pas une
erreur de configuration. Piste si on veut la débloquer : embeddings
OpenAI (si OPENAI_API_KEY est défini) plutôt que FastEmbed pour ce script
précis. Voir *Limites et pistes* dans le README.
"""

import argparse
import json
import time

from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness
from ragas.run_config import RunConfig

from src import config
from src.rag_chain import build_rag_chain, build_retriever, get_llm
from src.vector_store import get_vector_store

QUESTIONS_FILE = config.BASE_DIR / "eval" / "questions.json"
RESULTS_FILE = config.BASE_DIR / "eval" / "results_ragas.md"


def build_dataset(chain, sample_size: int) -> EvaluationDataset:
    """
    Un seul appel par question (chain.invoke), pas un appel retriever puis
    un appel chain séparés : même principe que le correctif V1.1 de
    rag_chain.py (ne jamais interroger la base deux fois pour une question).
    """
    data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    questions = data["in_scope"][:sample_size]

    rows = []
    for q in questions:
        time.sleep(2)  # reste sous la limite de requêtes/minute du tier gratuit Groq
        result = chain.invoke(q["question"])
        rows.append(
            {
                "user_input": q["question"],
                "retrieved_contexts": [p["content"] for p in result["passages"]],
                "response": result["answer"],
            }
        )
    return EvaluationDataset.from_list(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue la fidélité des réponses au contexte avec RAGAS.")
    parser.add_argument("--sample", type=int, default=8, help="nombre de questions à évaluer (défaut : 8)")
    args = parser.parse_args()

    # max_tokens plus généreux que le défaut : le LLM-juge RAGAS répond en
    # JSON structuré (affirmations + verdicts), plus long qu'une réponse
    # normale de l'app. Voir le docstring de ce module et de get_llm().
    llm = get_llm(max_tokens=8192)
    vector_store = get_vector_store()
    chain = build_rag_chain(retriever=build_retriever(vector_store), llm=llm)

    dataset = build_dataset(chain, args.sample)

    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness()],
        llm=LangchainLLMWrapper(llm),
        run_config=RunConfig(max_workers=1, timeout=180),
    )

    df = result.to_pandas()
    lines = [
        f"## Qualité des réponses (RAGAS) — {len(df)} questions, {config.LLM_MODEL_NAME}\n",
        "| Métrique | Score moyen |",
        "|---|---|",
        f"| Faithfulness (fidélité au contexte) | {df['faithfulness'].mean():.2f} |",
        "\nDétail par question :\n",
        "| Question | Faithfulness |",
        "|---|---|",
    ]
    for _, row in df.iterrows():
        lines.append(f"| {row['user_input']} | {row.get('faithfulness', float('nan')):.2f} |")

    report = "\n".join(lines)
    print(report)
    RESULTS_FILE.write_text(report + "\n", encoding="utf-8")
    print(f"\nRésultats enregistrés dans {RESULTS_FILE.relative_to(config.BASE_DIR)}")


if __name__ == "__main__":
    main()
