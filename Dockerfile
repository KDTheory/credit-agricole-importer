FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ajoutez un script pour générer la configuration
COPY generate_config.sh /app/generate_config.sh
RUN chmod +x /app/generate_config.sh

# Utilisez le script comme point d'entrée
ENTRYPOINT ["/app/generate_config.sh"]
CMD ["python", "main.py"]
