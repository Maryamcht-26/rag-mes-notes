FROM python:3.10-slim

WORKDIR /app

# Dépendances d'abord : cette couche reste en cache tant que
# requirements.txt ne change pas, même si le code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/documents/ data/documents/
COPY eval/ eval/
COPY app.py .

EXPOSE 8501

# Indexe les documents au démarrage, puis lance l'interface web.
# La clé API est passée à l'exécution (--env-file .env), jamais copiée dans l'image.
CMD ["sh", "-c", "python -m src.build_index && streamlit run app.py --server.address=0.0.0.0 --server.port=8501"]
