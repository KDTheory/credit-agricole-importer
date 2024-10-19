#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import logging
import sys
from creditagricole import CreditAgricoleClient
import firefly_iii_client
import urllib3
import requests

# Constants
CONFIG_FILE = '/app/config.ini'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mask_sensitive_info(text):
    # Masquer les numéros de compte
    masked_text = ' '.join(['XXXXXXXX' + s[-4:] if s.isdigit() and len(s) > 8 else s for s in text.split()])
    # Masquer les soldes
    masked_text = masked_text.replace(r'\d+\.\d+', 'XXX.XX')
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

def get_or_create_firefly_account(firefly_client, ca_account):
    try:
        firefly_accounts = firefly_client.get_accounts()
        for account in firefly_accounts:
            if account['attributes']['account_number'] == ca_account.numeroCompte:
                logger.info(f"Compte Firefly existant trouvé pour {mask_sensitive_info(ca_account.numeroCompte)}")
                return account['id']

        # Si le compte n'existe pas, on le crée
        new_account_data = {
            "name": ca_account.account['libelleProduit'],
            "type": "asset",
            "account_number": ca_account.numeroCompte,
            "opening_balance": str(ca_account.account['solde']),
            "currency_code": "EUR"
        }
        new_account = firefly_client.create_account(new_account_data)
        logger.info(f"Nouveau compte Firefly créé pour {mask_sensitive_info(ca_account.numeroCompte)}")
        return new_account['id']
    except Exception as e:
        logger.error(f"Erreur lors de la création/récupération du compte Firefly : {str(e)}")
        return None

def main():
    try:
        logger.info("Démarrage de l'importation des données du Crédit Agricole")
        
        config = load_config()
        
        # Initialisation du client Crédit Agricole
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
        
        # Récupération des comptes
        accounts = ca_cli.get_accounts()
        logger.info(f"Nombre de comptes récupérés : {len(accounts)}")
        
        # Initialisation du client Firefly III
        firefly_client = init_firefly_client(config)
        
        for account in accounts:
            try:
                logger.info(f"Traitement du compte: {mask_sensitive_info(account.numeroCompte)} - Solde: {mask_sensitive_info(str(account.account['solde']))} {account.account['libelleDevise']}")
                
                firefly_account_id = get_or_create_firefly_account(firefly_client, account)
                if not firefly_account_id:
                    logger.error(f"Impossible de traiter le compte {mask_sensitive_info(account.numeroCompte)}: échec de création/récupération dans Firefly")
                    continue

                # Récupération et importation des transactions
                transactions = ca_cli.get_transactions(account)
                logger.info(f"Nombre de transactions récupérées : {len(transactions)}")
                
                imported_count = 0
                for transaction in transactions:
                    try:
                        transaction_data = {
                            "transactions": [{
                                "type": "withdrawal" if transaction.amount < 0 else "deposit",
                                "date": transaction.date.strftime("%Y-%m-%d"),
                                "amount": str(abs(transaction.amount)),
                                "description": transaction.label,
                                "source_id": firefly_account_id if transaction.amount < 0 else None,
                                "destination_id": firefly_account_id if transaction.amount >= 0 else None,
                                "source_name": "External Account" if transaction.amount >= 0 else None,
                                "destination_name": "External Account" if transaction.amount < 0 else None
                            }]
                        }
                        firefly_client.create_transaction(transaction_data)
                        imported_count += 1
                    except requests.RequestException as e:
                        logger.error(f"Erreur lors de l'importation de la transaction: {str(e)}")
                
                logger.info(f"Transactions importées pour le compte {mask_sensitive_info(account.numeroCompte)}: {imported_count}/{len(transactions)}")
            
            except Exception as e:
                logger.error(f"Erreur lors du traitement du compte {mask_sensitive_info(account.numeroCompte)}: {str(e)}")
        
        logger.info("Importation terminée avec succès")
    
    except Exception as e:
        logger.exception("Une erreur s'est produite lors de l'importation")
        sys.exit(1)

if __name__ == '__main__':
    main()
