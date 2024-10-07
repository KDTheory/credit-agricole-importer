#!/bin/bash

# Générer le fichier config.ini à partir des variables d'environnement
cat << EOF > /app/config.ini
[FireflyIII]
url = ${FIREFLY_III_URL}
access_token = ${FIREFLY_III_ACCESS_TOKEN}

[CreditAgricole]
username = ${CREDIT_AGRICOLE_USERNAME}
password = ${CREDIT_AGRICOLE_PASSWORD}
EOF

# Exécuter la commande passée en argument
exec "$@"
