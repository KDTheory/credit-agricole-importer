#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import logging
import sys
from creditagricole import CreditAgricoleClient
import firefly_iii_client
import urllib3
import requests
from datetime import datetime
from dateutil import parser

# Constants
CONFIG_FILE = '/app/config.ini'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mask_sensitive_info(text):
    masked_text = ' '.join(['XXXXXXXX' + s[-4:] if s.isdigit() and len(s) > 8 else 'XXX.XX' if '.' in s and s.replace('.', '', 1).isdigit() else s for s in text.split()])
    return masked_text

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config

def init_firefly_client(config):
    try:
        firefly_section = config['FireflyIII']
        url = firefly_section.get('url')
        personal_access_token = firefly_section.get('personal_access_token')
        if not url or not personal_access_token:
            raise ValueError("URL ou token d'accès personnel manquant dans la configuration FireflyIII.")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session = requests.Session()
        session.headers.update({
            'Authorization': f"Bearer {personal_access_token}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        session.verify = False
        logger.info(f"Client Firefly III initialisé - URL: {mask_sensitive_info(url)}")
        return FireflyIIIClient(url, session)
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du client Firefly III : {str(e)}")
        raise

class FireflyIIIClient:
    def __init__(self, base_url, session):
        self.base_url = base_url
        self.session = session

    def get_accounts(self):
        response = self.session.get(f"{self.base_url}/api/v1/accounts")
        response.raise_for_status()
        return response.json()['data']

    def create_account(self, account_data):
        response = self.session.post(f"{self.base_url}/api/v1/accounts", json=account_data)
        response.raise_for_status()
        return response.json()['data']

    def create_transaction(self, transaction_data):
        response = self.session.post(f"{self.base_url}/api/v1/transactions", json=transaction_data)
        response.raise_for_status()
        return response.json()['data']

    def get_transactions(self, account_id):
        transactions = []
        page = 1
        while True:
            response = self.session.get(f"{self.base_url}/api/v1/accounts/{account_id}/transactions?page={page}")
            response.raise_for_status()
            data = response.json()
            if 'data' not in data:
                logger.warning(f"Aucune donnée de transaction retournée pour le compte Firefly ID: {account_id}")
                break
            transactions.extend(data['data'])
            if not data['meta']['pagination'].get('has_more_pages', False):
                break
            page += 1
        logger.info(f"{len(transactions)} transactions récupérées pour le compte Firefly ID {account_id}")
        return transactions

def get_or_create_firefly_account(firefly_client, ca_account):
    try:
        firefly_accounts = firefly_client.get_accounts()
        for account in firefly_accounts:
            if account['attributes'].get('account_number') == ca_account.numeroCompte:
                logger.info(f"Compte Firefly existant trouvé pour {mask_sensitive_info(ca_account.numeroCompte)}")
                return account['id']
        
        solde = ca_account.account.get('solde') or ca_account.account.get('valorisation') or ca_account.account.get('balance') or '0.00'
        
        if solde == '0.00' or solde is None:
            logger.warning(f"Le compte {mask_sensitive_info(ca_account.numeroCompte)} n'a pas de solde disponible. Il sera ignoré.")
            return None
        
        new_account_data = {
            "name": ca_account.account.get('libelleProduit', 'Compte sans nom'),
            "type": "asset",
            "account_number": ca_account.numeroCompte,
            "opening_balance": str(solde),
            "opening_balance_date": datetime.now().strftime('%Y-%m-%d'),
            "account_role": "defaultAsset",
            "currency_code": "EUR"
        }
        
        new_account = firefly_client.create_account(new_account_data)
        
        logger.info(f"Nouveau compte Firefly créé pour {mask_sensitive_info(ca_account.numeroCompte)} avec solde masqué {mask_sensitive_info(str(solde))}")
        
        return new_account['id']
    
    except requests.HTTPError as e:
        logger.error(f"Erreur lors de la création/récupération du compte Firefly : {e.response.status_code} {e.response.text}")
        return None
    
    except Exception as e:
        logger.error(f"Erreur inconnue lors de la création/récupération du compte Firefly : {str(e)}")
        return None

def main():
    try:
        logger.info("Démarrage de l'importation des données du Crédit Agricole")
        
        config = load_config()
        
        ca_config = config['CreditAgricole']
        
        ca_cli = CreditAgricoleClient(config)
        
        ca_cli.department = ca_config['department']
        
        ca_cli.account_id = ca_config['username']
        
        ca_cli.password = ca_config['password']
        
        ca_cli.enabled_accounts = ca_config.get('import_account_id_list', '')
        
        ca_cli.get_transactions_period = ca_config.get('get_transactions_period_days', '30')
        
        ca_cli.max_transactions = ca_config.get('max_transactions_per_get', '300')
        
        ca_cli.validate()
        
        ca_cli.init_session()
        
        logger.info("Client Crédit Agricole initialisé et session ouverte")
        
        accounts = ca_cli.get_accounts()
        
        logger.info(f"Nombre de comptes récupérés : {len(accounts)}")
        
        firefly_client = init_firefly_client(config)

        for account in accounts:
            
            if not account.account:
                logger.warning(f"Le compte {mask_sensitive_info(account.numeroCompte)} n'a pas d'informations de compte disponibles. Il sera ignoré.")
                continue
            
            solde = account.account.get('solde') or account.account.get('valorisation') or account.account.get('balance') or '0.00'
            
            libelle_devise = account.account.get('libelleDevise', 'Devise inconnue')
            
            logger.info(f"Traitement du compte:... {mask_sensitive_info(account.numeroCompte)} - Solde masqué: {mask_sensitive_info(str(solde))} {libelle_devise}")
            
            firefly_account_id = get_or_create_firefly_account(firefly_client, account)
            
            if not firefly_account_id:
                logger.error(f"Impossible de traiter le compte {mask_sensitive_info(account.numeroCompte)}: échec de création/récupération dans Firefly")
                continue
            
            # Collecte des transactions existantes dans Firefly
            logger.info("Récupération des transactions existantes dans Firefly")
            existing_transactions = firefly_client.get_transactions(firefly_account_id)

            # Création de l'ensemble des transactions existantes pour la comparaison
            existing_set = set()

            for tx in existing_transactions:
                # Récupérer les attributs nécessaires depuis le sous-ensemble 'transactions'
                transaction_details = tx['attributes'].get('transactions', [])
                
                if not transaction_details:
                    logger.warning(f"Transaction sans détails trouvée et ignorée : {tx}")
                    continue

                for detail in transaction_details:
                    date = detail.get('date')
                    amount = detail.get('amount')
                    description = detail.get('description')

                    # Standardiser les champs pour éviter les différences mineures
                    if date and amount and description:
                        # Convertir la date au format standard YYYY-MM-DD
                        standardized_date = parser.parse(date).strftime("%Y-%m-%d")
                        
                        # Convertir le montant en float pour éviter les différences d'arrondi
                        standardized_amount = f"{float(amount):.2f}"
                        
                        # Nettoyer la description en supprimant les espaces superflus
                        standardized_description = description.strip()
                        
                        transaction_tuple = (standardized_date, standardized_amount, standardized_description)
                        existing_set.add(transaction_tuple)
                        logger.debug(f"Transaction existante ajoutée pour comparaison : {transaction_tuple}")
                    else:
                        # Enregistrer un message d'avertissement avec plus de détails sur la transaction incomplète
                        logger.warning(f"Transaction incomplète ignorée lors de la comparaison des doublons : {detail}")
            
            logger.info(f"{len(existing_set)} transactions existantes chargées pour comparaison des doublons.")
            
            transactions = ca_cli.get_transactions(account)
            
            imported_count = 0
            
            for transaction in transactions:
                try:
                    montant = transaction.montantOp
                    
                    # Standardiser la date au format YYYY-MM-DD
                    date_operation = parser.parse(transaction.dateOp) if isinstance(transaction.dateOp, str) else transaction.dateOp
                    standardized_date = date_operation.strftime("%Y-%m-%d")
                    
                    # Convertir le montant en float pour éviter les différences d'arrondi
                    standardized_amount = f"{abs(float(montant)):.2f}"
                    
                    # Nettoyer la description en supprimant les espaces superflus
                    libelle = transaction.libelleOp.strip()

                    transaction_key = (standardized_date, standardized_amount, libelle)
                    
                    # Vérification des doublons avant l'importation
                    if transaction_key in existing_set:
                        masked_transaction_key = tuple(mask_sensitive_info(str(item)) for item in transaction_key)
                        logger.info(f"Doublon détecté pour la transaction : {masked_transaction_key}. Ignorée.")
                        continue

                    transaction_data = {
                        "transactions": [{
                            "type": "withdrawal" if montant < 0 else "deposit",
                            "date": standardized_date,
                            "amount": standardized_amount,
                            "description": libelle,
                            "source_id": firefly_account_id if montant < 0 else None,
                            "destination_id": firefly_account_id if montant >= 0 else None,
                        }]
                    }
                    
                    firefly_client.create_transaction(transaction_data)
                    imported_count += 1
                
                except requests.RequestException as e:
                    logger.error(f"Erreur lors de l'importation de la transaction: {str(e)}")
            
            logger.info(f"Transactions importées pour le compte {mask_sensitive_info(account.numeroCompte)}: {imported_count}/{len(transactions)}")
    
    except Exception as e:
        logger.exception("Une erreur s'est produite lors de l'importation")
    
if __name__ == '__main__':
    main()