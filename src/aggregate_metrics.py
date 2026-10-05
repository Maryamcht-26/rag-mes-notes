"""
Agrège logs/metrics.jsonl (écrit par src/observability.py à chaque
question posée via l'app ou la CLI) en statistiques lisibles.

Usage :
    python -m src.aggregate_metrics

N'affiche que des chiffres et du texte fixe (pas de réponse du LLM) :
pas besoin du correctif stdout UTF-8 des autres scripts d'évaluation.
"""

import json
from statistics import mean

from src import config
from src.observability import METRICS_FILE


def main() -> None:
    if not METRICS_FILE.exists():
        print(
            f"Aucun log trouvé ({METRICS_FILE.relative_to(config.BASE_DIR)}) : "
            "pose au moins une question via l'app (streamlit run app.py) ou la CLI (python -m src.cli) d'abord."
        )
        return

    lines = [line for line in METRICS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries = [json.loads(line) for line in lines]
    if not entries:
        print("Fichier de logs vide.")
        return

    print(f"{len(entries)} question(s) journalisée(s) dans {METRICS_FILE.relative_to(config.BASE_DIR)}\n")
    print(f"Latence moyenne      : {mean(e['elapsed_seconds'] for e in entries):.2f} s")
    print(f"Latence max          : {max(e['elapsed_seconds'] for e in entries):.2f} s")
    print(f"Tokens moyens / question : {mean(e['total_tokens'] for e in entries):.0f}")
    print(f"  dont raisonnement      : {mean(e['reasoning_tokens'] for e in entries):.0f}")
    print(f"Tokens totaux         : {sum(e['total_tokens'] for e in entries)}")
    print(f"Passages moyens       : {mean(e['num_passages'] for e in entries):.1f}")


if __name__ == "__main__":
    main()
