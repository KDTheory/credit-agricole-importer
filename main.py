import configparser
import os
import sys
import time
import firefly_iii_client
import tool
import logging
from constant import *
from creditagricole import CreditAgricoleClient
from firefly3 import Firefly3Client, Firefly3Importer
from firefly_iii_client.api import accounts_api, transactions_api
from firefly_iii_client.configuration import Configuration
from firefly_iii_client import AccountStore, AccountUpdate, TransactionStore, TransactionSplitStore
from collections import defaultdict
from logger import Logger

# Random log to make sure this script is running
print("Python version:", sys.version)
print("Starting main.py")
sys.stdout.flush()
sys.stderr.flush()

# Read configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Configure logging
log_file = '/app/importer.log'
print(f"Attempting to log to: {log_file}")
print(f"Log file exists: {os.path.exists(log_file)}")
print(f"Log file is writable: {os.access(log_file, os.W_OK)}")

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler(sys.stdout)
                    ])

logger = logging.getLogger(__name__)
logger.info("Logging initialized in main.py")

# Firefly III API client configuration
configuration = Configuration(
    host=config.get('FireflyIII', 'url')
)
configuration.access_token = config.get('FireflyIII', 'personal_access_token')

with firefly_iii_client.ApiClient(configuration) as api_client:
    
    def get_or_create_account(accounts_api, name, type, iban=None):
        try:
            # Try to find the account by name
            accounts = accounts_api.list_account(query=name)
            for account in accounts.data:
                if account.attributes.name == name:
                    logger.info(f"Account '{name}' already exists.")
                    return account.id
            
            # If not found, create a new account
            new_account = account_store.AccountStore(
                name=name,
                type=type,
                iban=iban
            )
            response = accounts_api.store_account(new_account)
            logger.info(f"Created new account '{name}'.")
            return response.data.id
        except firefly_iii_client.ApiException as e:
            logger.error(f"Exception when calling AccountsApi: {e}")
            return None
    
    def update_account_balance(accounts_api, account_id, balance):
        try:
            update = account_update.AccountUpdate(current_balance=balance)
            accounts_api.update_account(account_id, update)
            logger.info(f"Updated balance for account {account_id}")
        except firefly_iii_client.ApiException as e:
            logger.error(f"Exception when updating account balance: {e}")
    
    def main():
        try:
            logger.info("Démarrage de l'importation des données du Crédit Agricole")
            
            ca_cli = CreditAgricoleClient(config)
            logger.info("Client Crédit Agricole initialisé")
            
            ca_cli.init_session()
            logger.info("Session Crédit Agricole initialisée")
            
            accounts = ca_cli.get_accounts()
            logger.info(f"Nombre de comptes récupérés : {len(accounts)}")
            
            for account in accounts:
                account_info = f"Compte: {account.get_product_name()} - Solde: {account.get_balance()}"
                logger.info(account_info)
                
                # Récupérer les transactions pour chaque compte
                try:
                  transactions = account.get_operations(count=300)  # Récupère les 300 dernières opérations
                  logger.info(f"Nombre de transactions récupérées pour le compte {account.numero}: {len(transactions)}")
              
                  for transaction in transactions:
                      logger.info(f"Transaction: Date={transaction.get_date()}, Montant={transaction.get_amount()}, Libellé={transaction.get_label()}")
                
                # Importation dans Firefly III
                firefly_cli = FireflyIIIClient(config)
                imported_count = firefly_cli.import_transactions(transactions)
                logger.info(f"Nombre de transactions importées dans Firefly III : {imported_count}")
                
                logger.info("Importation terminée avec succès")
              
        except Exception as e:
            logger.exception("Une erreur s'est produite lors de l'importation")
            sys.exit(1)
            verify_import(firefly_cli, imported_count)
      
            # Close Crédit Agricole session
            ca_cli.close_session()
    
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            sys.exit(1)

    def verify_import(firefly_cli, imported_count):
        logger.info("Vérification de l'importation")
        firefly_transactions_count = firefly_cli.get_transactions_count()
        if firefly_transactions_count >= imported_count:
            logger.info(f"Vérification réussie : {firefly_transactions_count} transactions trouvées dans Firefly III")
        else:
            logger.warning(f"Vérification échouée : seulement {firefly_transactions_count} transactions trouvées dans Firefly III au lieu de {imported_count}")
  
    if __name__ == "__main__":
        main()
