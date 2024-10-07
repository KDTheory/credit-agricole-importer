# Importateur Crédit Agricole - Dockerfile

FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier des dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Créer le fichier de configuration
RUN echo "[GlobalSettings]\nusername=${CREDIT_AGRICOLE_USERNAME}\npassword=${CREDIT_AGRICOLE_PASSWORD}\n" > config.ini && \
    echo "[CreditAgricole]\n# Ajoutez ici les options spécifiques à Crédit Agricole\n" >> config.ini

# Commande pour exécuter le script
CMD ["python", "main.py"]
