#!/bin/bash

# Fonction pour exécuter le script Python
run_script() {
    python /app/main.py
}

# Exécuter le script au démarrage
run_script

# Boucle pour exécuter le script toutes les heures
while true; do
    sleep 3600  # Attendre 1 heure (3600 secondes)
    run_script
done
