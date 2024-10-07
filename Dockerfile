# Utiliser une image de base officielle de Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requis pour l'application
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Créer le fichier de configuration config.ini
RUN echo "[default]\nusername = ${CREDIT_AGRICOLE_USERNAME}\npassword = ${CREDIT_AGRICOLE_PASSWORD}" > config.ini

# Commande pour exécuter le script
CMD ["python", "main.py"]
