#!/bin/bash

# Définir le chemin du fichier de configuration
CONFIG_FILE="/app/config.ini"

# Fonction pour ajouter ou mettre à jour une section
update_section() {
    local section=$1
    local key=$2
    local value=$3
    
    if ! grep -q "\[$section\]" "$CONFIG_FILE"; then
        echo "" >> "$CONFIG_FILE"
        echo "[$section]" >> "$CONFIG_FILE"
    fi
    
    if grep -q "^$key\s*=" "$CONFIG_FILE"; then
        sed -i "s|^$key\s*=.*|$key = $value|" "$CONFIG_FILE"
    else
        echo "$key = $value" >> "$CONFIG_FILE"
    fi
}

# Créer ou vider le fichier de configuration
> "$CONFIG_FILE"

# Section GlobalSettings
update_section "GlobalSettings" "debug" "${DEBUG:-false}"
update_section "GlobalSettings" "dry_run" "${DRY_RUN:-false}"

# Section FireflyIII
update_section "FireflyIII" "url" "${FIREFLY_III_URL}"
update_section "FireflyIII" "access_token" "${FIREFLY_III_ACCESS_TOKEN}"

# Section CreditAgricole
update_section "CreditAgricole" "username" "${CREDIT_AGRICOLE_USERNAME}"
update_section "CreditAgricole" "password" "${CREDIT_AGRICOLE_PASSWORD}"

# Ajouter la section AutoRenameTransaction
update_section "AutoRenameTransaction" "enabled" "${AUTO_RENAME_ENABLED:-false}"
update_section "AutoRenameTransaction" "rules" "${AUTO_RENAME_RULES:-}"

# Afficher le contenu du fichier de configuration (pour le débogage)
echo "Contenu du fichier de configuration :"
cat "$CONFIG_FILE"

# Exécuter la commande principale
exec "$@"
