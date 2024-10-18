#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import logging
import os
import sys
from creditagricole import CreditAgricoleClient
import firefly_iii_client
print(f"Version de firefly-iii-client : {firefly_iii_client.__version__}")
from firefly_iii_client import Configuration
from firefly_iii_client.api import accounts_api, transactions_api, configuration_api
import urllib3
import requests

# Constants
CONFIG_FILE = '/app/config.ini'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config
    
    return {
        "firefly_url": config['FireflyIII'].get('url'), 
        "firefly_token": config['FireflyIII'].get('personal_access_token'),
    }

def init_firefly_client(config):
    try:
        firefly_section = config['FireflyIII']
        url = firefly_section.get('url')
        personal_access_token = firefly_section.get('personal_access_token')

        if not url or not personal_access_token:
            raise ValueError("URL ou token d'accès personnel manquant dans la configuration FireflyIII.")

        # Désactiver les avertissements liés à l'insécurité SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        session = requests.Session()
        session.headers.update({
            'Authorization': f"Bearer {personal_access_token}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        session.verify = False  # Désactive la vérification SSL

        print("Configuration Firefly III :")
        print("URL:", url)
        
        return FireflyIIIClient(url, session)
    except Exception as e:
        print(f"Erreur lors de l'initialisation du client Firefly III : {e}")
        raise

class FireflyIIIClient:
    def __init__(self, base_url, session):
        self.base_url = base_url
        self.session = session

    def get_accounts(self):
        response = self.session.get(f"{self.base_url}/api/v1/accounts")
        response.raise_for_status()
        return response.json()['data']

    def create_transaction(self, transaction_data):
        response = self.session.post(f"{self.base_url}/api/v1/transactions", json=transaction_data)
        response.raise_for_status()
        return response.json()['data']

def import_transactions(transactions_api_instance, account, transactions):
    imported_count = 0
    for transaction in transactions:
        try:
            transaction_split = TransactionSplitStore(
                type="withdrawal" if transaction.amount < 0 else "deposit",
                date=transaction.date.strftime("%Y-%m-%d"),
                amount=str(abs(transaction.amount)),
                description=transaction.label,
                source_name=account.name if transaction.amount < 0 else "External Account",
                destination_name="External Account" if transaction.amount < 0 else account.name
            )
            transactions_api_instance.store_transaction(transaction_split_store=transaction_split)
            imported_count += 1
        except firefly_iii_client.ApiException as e:
            logger.error(f"Exception lors de l'importation de la transaction: {e}")
    return imported_count

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
        logger.info("Client Crédit Agricole initialisé")
        
        # Initialisation de la session
        ca_cli.init_session()
        logger.info("Session Crédit Agricole initialisée")
        
        # Récupération des comptes
        accounts = ca_cli.get_accounts()
        logger.info(f"Nombre de comptes récupérés : {len(accounts)}")
        for account in accounts:
            logger.info(f"Attributs du compte : {vars(account)}")
        
        # Initialisation du client Firefly III
        api_client = init_firefly_client(config)
        transactions_api = firefly_iii_client.TransactionsApi(api_client)
        
for account in accounts:
    try:
        # Utilisez les attributs corrects de l'objet Account
        account_info = f"Compte: {account.id} - Solde: {account.balance}"
        logger.info(account_info)
        
        # Récupération des transactions pour chaque compte
        transactions = ca_cli.get_transactions(account)
        logger.info(f"Nombre de transactions récupérées pour le compte {account.id}: {len(transactions)}")
        
        # Importation des transactions dans Firefly III
        for transaction in transactions:
            try:
                transaction_data = {
                    "transactions": [{
                        "type": "withdrawal" if transaction.amount < 0 else "deposit",
                        "date": transaction.date.strftime("%Y-%m-%d"),
                        "amount": str(abs(transaction.amount)),
                        "description": transaction.label,
                        "source_name": account.id if transaction.amount < 0 else "External Account",
                        "destination_name": "External Account" if transaction.amount < 0 else account.id
                    }]
                }
                response = firefly_client.create_transaction(transaction_data)
                logger.info(f"Transaction importée : {response}")
            except requests.RequestException as e:
                logger.error(f"Erreur lors de l'importation de la transaction: {e}")
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du compte : {str(e)}")
        logger.error(f"Détails du compte: {vars(account)}")
        
        logger.info("Importation terminée avec succès")
    
    except Exception as e:
        logger.exception("Une erreur s'est produite lors de l'importation")
        sys.exit(1)

if __name__ == '__main__':
    main()
