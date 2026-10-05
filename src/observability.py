"""
Journalisation structurée des questions posées via l'app ou la CLI :
latence, tokens consommés, nombre de passages retrouvés. Une question =
une ligne JSON ajoutée à logs/metrics.jsonl (format JSON Lines : facile à
agréger avec src/aggregate_metrics.py, ou à rebrancher plus tard sur un
vrai outil comme Langfuse — voir *Limites et pistes* dans le README).

Pourquoi pas de simples print() ? Un print() est lu par un humain, une
fois, dans un terminal qui défile. Un log structuré (une ligne JSON par
question) est relisible PAR UN PROGRAMME, comme le ferait un vrai outil
d'observabilité avec bien plus de requêtes qu'un humain ne peut en
suivre à l'œil.

Les tokens sont capturés via un callback LangChain (on_llm_end), PAS en
lisant result["answer"] : la chaîne passe par StrOutputParser() qui
réduit la réponse du LLM à une simple chaîne de caractères AVANT de nous
revenir — à ce stade, les métadonnées (tokens, etc.) de la réponse brute
sont déjà perdues. Le callback, lui, intercepte la réponse du LLM au
moment où elle sort du modèle, avant cette perte d'information.
"""

import json
import logging
import time

from langchain_core.callbacks import BaseCallbackHandler

from src import config

LOG_DIR = config.BASE_DIR / "logs"
METRICS_FILE = LOG_DIR / "metrics.jsonl"

# basicConfig configure le logger RACINE : le laisser à WARNING évite que
# les librairies tierces (httpx, chromadb...) se mettent aussi à logguer
# chaque requête HTTP sur la console dès qu'on importe ce module. Seul
# notre logger "rag" est explicitement remonté à INFO.
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("rag")
logger.setLevel(logging.INFO)


class _UsageTracker(BaseCallbackHandler):
    """Additionne les tokens de chaque appel LLM déclenché pendant une invocation de chaîne."""

    def __init__(self) -> None:
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.reasoning_tokens = 0

    def on_llm_end(self, response, **kwargs) -> None:
        for generations in response.generations:
            for generation in generations:
                message = getattr(generation, "message", None)
                usage = getattr(message, "usage_metadata", None) or {}
                self.prompt_tokens += usage.get("input_tokens", 0)
                self.completion_tokens += usage.get("output_tokens", 0)
                self.total_tokens += usage.get("total_tokens", 0)
                # Spécifique aux modèles "de raisonnement" (ex. openai/gpt-oss-20b
                # sur Groq) : tokens dépensés à "réfléchir" avant de répondre,
                # invisibles dans la réponse mais bien facturés. Absent pour
                # les modèles classiques, d'où le .get(..., {}) imbriqué.
                details = getattr(message, "response_metadata", {}).get("token_usage", {}).get(
                    "completion_tokens_details"
                ) or {}
                self.reasoning_tokens += details.get("reasoning_tokens", 0)


def timed_ask(chain, question: str) -> dict:
    """
    Enveloppe chain.invoke(question) : mesure la latence, capture les
    tokens via un callback, journalise le tout, et renvoie le résultat
    EXACTEMENT comme chain.invoke seul — app.py et cli.py n'ont rien
    d'autre à changer que d'appeler cette fonction (déjà fait dans
    rag_chain.ask(), leur point d'entrée commun).
    """
    LOG_DIR.mkdir(exist_ok=True)
    tracker = _UsageTracker()

    started = time.perf_counter()
    result = chain.invoke(question, config={"callbacks": [tracker]})
    elapsed = time.perf_counter() - started

    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_seconds": round(elapsed, 2),
        "num_passages": len(result.get("passages", [])),
        "num_sources": len(result.get("sources", [])),
        "prompt_tokens": tracker.prompt_tokens,
        "completion_tokens": tracker.completion_tokens,
        "reasoning_tokens": tracker.reasoning_tokens,
        "total_tokens": tracker.total_tokens,
        "llm_provider": config.LLM_PROVIDER,
        "llm_model": config.LLM_MODEL_NAME,
    }
    with METRICS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(
        "question traitée en %.2fs — %d tokens (dont %d de raisonnement), %d passages",
        elapsed,
        tracker.total_tokens,
        tracker.reasoning_tokens,
        entry["num_passages"],
    )
    return result
