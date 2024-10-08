import configparser
import os
import time
import firefly_iii_client
import tool
import logging
from constant import *
from creditagricole import CreditAgricoleClient
from firefly3 import Firefly3Client, Firefly3Importer
from firefly_iii_client.api import accounts_api, transactions_api
from firefly_iii_client import AccountStore, AccountUpdate, TransactionStore, TransactionSplitStore
from collections import defaultdict
from logger import Logger

# Read configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Configure logging
logging.basicConfig(
    level=config.get('Logging', 'level', fallback='INFO'),
    filename=config.get('Logging', 'file', fallback=None),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Firefly III API client configuration
configuration = firefly_iii_client.Configuration(
    host=config.get('FireflyIII', 'url')
)
configuration.access_token = config.get('FireflyIII', 'personal_access_token')

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
        # Initialize Crédit Agricole client
        ca_cli = CreditAgricoleClient(config, logger)
        ca_cli.validate()
        ca_cli.init_session()

        with firefly_iii_client.ApiClient(configuration) as api_client:
            accounts_api_instance = accounts_api.AccountsApi(api_client)
            transactions_api_instance = transactions_api.TransactionsApi(api_client)

            # Get accounts from Crédit Agricole
            ca_accounts = ca_cli.get_accounts()

            for ca_account in ca_accounts:
                # Get or create account in Firefly III
                ff_account_id = get_or_create_account(accounts_api_instance, ca_account.label, "asset", ca_account.iban)
                if ff_account_id is None:
                    continue

                # Update account balance
                update_account_balance(accounts_api_instance, ff_account_id, str(ca_account.balance))

                # Get transactions for the account
                transactions = ca_cli.get_transactions(ca_account.id)

                for transaction in transactions:
                    # Create a new transaction in Firefly III
                    transaction_split = transaction_split_store.TransactionSplitStore(
                        amount=str(abs(transaction.amount)),
                        date=transaction.date.strftime("%Y-%m-%d"),
                        description=transaction.label,
                        source_id=ff_account_id if transaction.amount < 0 else None,
                        destination_id=ff_account_id if transaction.amount > 0 else None,
                        type="withdrawal" if transaction.amount < 0 else "deposit"
                    )

                    transaction_store_obj = transaction_store.TransactionStore(
                        transactions=[transaction_split]
                    )

                    try:
                        api_response = transactions_api_instance.store_transaction(transaction_store_obj)
                        logger.info(f"Transaction created successfully: {api_response}")
                    except firefly_iii_client.ApiException as e:
                        logger.error(f"Exception when creating transaction: {e}")

        # Close Crédit Agricole session
        ca_cli.close_session()

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
