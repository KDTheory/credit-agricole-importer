#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import logging
import os
import sys
from creditagricole import CreditAgricoleClient
import firefly_iii_client
from firefly_iii_client.api import accounts_api, transactions_api

# Constants
CONFIG_FILE = '/app/config.ini'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config

def init_firefly_client(config):
    firefly_section = config['FireflyIII']
    configuration = firefly_iii_client.Configuration(
        host=firefly_section['url'],
        api_key={'Authorization': f"Bearer {firefly_section['personal_access_token']}"}
    )
    return firefly_iii_client.ApiClient(configuration)

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
        
        # Initialisation du client Firefly III
        with init_firefly_client(config) as api_client:
            transactions_api_instance = transactions_api.TransactionsApi(api_client)
        
            for account in accounts:
                try:
                    account_info = f"Compte: {account.name} - Solde: {account.balance}"
                    logger.info(account_info)
                    
                    # Récupération des transactions pour chaque compte
                    transactions = ca_cli.get_transactions(account)
                    logger.info(f"Nombre de transactions récupérées pour le compte {account.name}: {len(transactions)}")
                    
                    # Importation des transactions dans Firefly III
                    imported_count = import_transactions(transactions_api_instance, account, transactions)
                    logger.info(f"Nombre de transactions importées dans Firefly III pour le compte {account.name} : {imported_count}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du compte {account.name}: {str(e)}")
        
        logger.info("Importation terminée avec succès")
    
    except Exception as e:
        logger.exception("Une erreur s'est produite lors de l'importation")
        sys.exit(1)

if __name__ == '__main__':
    main()
