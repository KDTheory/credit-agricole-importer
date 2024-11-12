#!/bin/bash

echo "Starting entrypoint script"

# Fonction pour exécuter le script Python
run_script() {
    echo "Running main.py"
    python /app/main.py
    echo "main.py execution completed"
}

# Configuration de cron pour exécuter le script à 8h tous les jours
# Redirection des logs vers stdout/stderr au lieu d'un fichier
echo "0 8 * * * /bin/bash -c 'python /app/main.py' >> /proc/1/fd/1 2>&1" | crontab -

# Démarrer cron en arrière-plan
echo "Starting cron service"
cron -f  # Démarrer cron au premier plan

# Garder le conteneur actif (plus besoin de tail)
