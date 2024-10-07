#!/bin/bash

CONFIG_FILE="/app/config.ini"

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

> "$CONFIG_FILE"

# GlobalSettings
update_section "GlobalSettings" "debug" "${DEBUG:-false}"
update_section "GlobalSettings" "dry_run" "${DRY_RUN:-false}"

# FireflyIII
update_section "FireflyIII" "url" "${FIREFLY_III_URL}"
update_section "FireflyIII" "access_token" "${FIREFLY_III_ACCESS_TOKEN}"

# CreditAgricole
update_section "CreditAgricole" "username" "${CREDIT_AGRICOLE_USERNAME}"
update_section "CreditAgricole" "password" "${CREDIT_AGRICOLE_PASSWORD}"

# AutoRenameTransaction
update_section "AutoRenameTransaction" "enabled" "${AUTO_RENAME_ENABLED:-false}"
update_section "AutoRenameTransaction" "rules" "${AUTO_RENAME_RULES:-}"

# AutoAssignBudget
update_section "AutoAssignBudget" "enabled" "${AUTO_ASSIGN_BUDGET_ENABLED:-false}"
update_section "AutoAssignBudget" "rules" "${AUTO_ASSIGN_BUDGET_RULES:-}"

# AutoAssignCategory
update_section "AutoAssignCategory" "enabled" "${AUTO_ASSIGN_CATEGORY_ENABLED:-false}"
update_section "AutoAssignCategory" "rules" "${AUTO_ASSIGN_CATEGORY_RULES:-}"

# AutoAssignTags
update_section "AutoAssignTags" "enabled" "${AUTO_ASSIGN_TAGS_ENABLED:-false}"
update_section "AutoAssignTags" "rules" "${AUTO_ASSIGN_TAGS_RULES:-}"

# AutoAssignAccount
update_section "AutoAssignAccount" "enabled" "${AUTO_ASSIGN_ACCOUNT_ENABLED:-false}"
update_section "AutoAssignAccount" "rules" "${AUTO_ASSIGN_ACCOUNT_RULES:-}"

# Logging
update_section "Logging" "level" "${LOGGING_LEVEL:-INFO}"
update_section "Logging" "file" "${LOGGING_FILE:-/app/importer.log}"

# Accounts
update_section "Accounts" "mapping" "${ACCOUNTS_MAPPING:-}"

echo "Contenu du fichier de configuration :"
cat "$CONFIG_FILE"

exec "$@"
