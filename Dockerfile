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

# Commande pour exécuter le script
CMD ["python", "main.py"]
