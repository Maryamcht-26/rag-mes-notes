## Retrieval — 22 questions, k=4

| Mode | Hit@1 | Hit@4 | MRR |
|---|---|---|---|
| dense | 68% | 91% | 0.76 |
| hybrid | 86% | 95% | 0.90 |

Passage non retrouvé en mode dense :
- Que signifie l'option -d ?
- Peut-on utiliser COUNT dans un WHERE ?

Passage non retrouvé en mode hybrid :
- Que signifie l'option -d ?

## Génération — openai/gpt-oss-20b, mode hybrid

| Métrique | Score |
|---|---|
| Réponses données (questions dans le périmètre) | 95% |
| Refus corrects (questions hors périmètre) | 100% |

Refus à tort :
- Que signifie l'option -d ?
