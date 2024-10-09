from datetime import datetime, timedelta

from creditagricole_particuliers import Authenticator, Accounts
from constant import *
import urllib.parse
import requests
import re
import logging
from urllib.parse import urljoin


class CreditAgricoleAuthenticator(Authenticator):
    def __init__(self, username, password, ca_region):
        """custom authenticator class"""
        self.url = "https://www.credit-agricole.fr"
        self.ssl_verify = True
        self.username = username
        self.password = password
        self.department = "none"
        self.regional_bank_url = "ca-" + ca_region
        self.cookies = None

        self.authenticate()


class CreditAgricoleClient:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.department = config.get('CreditAgricole', 'department')
        self.username = config.get('CreditAgricole', 'username')
        self.password = self.parse_password(config.get('CreditAgricole', 'password'))
        self.session = None

    def parse_password(self, password_string):
        return [int(char) for char in password_string if char.isdigit()]

    def log_message(self, level, message):
        if hasattr(self.logger, level):
            getattr(self.logger, level)(message)
        elif hasattr(self.logger, 'log'):
            log_levels = {
                'debug': logging.DEBUG,
                'info': logging.INFO,
                'warning': logging.WARNING,
                'error': logging.ERROR,
                'critical': logging.CRITICAL
            }
            self.logger.log(log_levels.get(level, logging.INFO), message)
        else:
            print(f"{level.upper()}: {message}")

    def validate(self):
        if not self.username or not self.password or not self.department:
            self.log_message('error', "Missing credentials")
            raise ValueError("Username, password, or department is missing")
        if not self.department.isdigit() or len(self.department) != 2:
            self.log_message('error', f"Invalid department number: {self.department}")
            raise ValueError(f"Invalid department number: {self.department}. It should be a two-digit number.")
        self.log_message('info', "Credentials validated")

    def init_session(self):
    try:
        username = self.config.get('CreditAgricole', 'username')
        password = self.config.get('CreditAgricole', 'password')
        department = self.config.get('CreditAgricole', 'department')
        
        self.logger.info(f"Initializing session with username: {username}, department: {department}")

        password_list = [int(char) for char in password]
        
        self.session = Authenticator(
            username=username,
            password=password_list,
            region=department
        )
        self.logger.info("Session Crédit Agricole initialisée avec succès")
    except Exception as e:
        self.logger.error(f"Erreur lors de l'initialisation de la session : {str(e)}")
        raise

    def get_accounts(self):
        self.logger.info("Récupération des comptes")
        if not self.session:
            self.logger.error("Session not initialized")
            raise ValueError("Session not initialized. Call init_session() first.")
        
        try:
            accounts = Accounts(session=self.session)
            return accounts.list
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des comptes : {str(e)}")
            raise

    def get_transactions(self, account_id):
        self.logger.info("Récupération des transactions")
        if not self.session:
            self.log_message('error', "Session not initialized")
            raise ValueError("Session not initialized. Call init_session() first.")
        try:
            transactions = self.session.get_transactions(account_id)
            self.log_message('info', f"Retrieved {len(transactions)} transactions for account {account_id}")
            return transactions
        except Exception as e:
            self.log_message('error', f"Failed to retrieve transactions for account {account_id}: {str(e)}")
            raise
        self.logger.info(f"Nombre total de transactions récupérées : {len(all_transactions)}")
        return all_transactions

    def close_session(self):
        if self.session:
            try:
                self.session.close()
                self.log_message('info', "Session closed successfully")
            except Exception as e:
                self.log_message('error', f"Failed to close session: {str(e)}")
        else:
            self.log_message('warning', "No active session to close")
            
class CreditAgricoleRegion:

    def __init__(self, ca_region):

        self.name = CA_REGIONS[ca_region]
        self.longitude = None
        self.latitude = None

        # Find the bank region location
        address = "Credit Agricole " + self.name + ", France"
        url = 'https://nominatim.openstreetmap.org/search.php?q=' + urllib.parse.quote(address) + '&format=jsonv2'
        response = requests.get(url).json()
        if len(response) > 0 and "lon" in response[0] and "lat" in response[0]:
            self.longitude = str(response[0]['lon'])
            self.latitude = str(response[0]['lat'])

    @staticmethod
    def get_ca_region(department_id: str):
        if department_id in CA_REGIONS.keys():
            return [department_id]
        department_id = str(int(department_id)) if department_id.isdigit() else department_id
        for key, value in DEPARTMENTS_TO_CA_REGIONS.items():
            if department_id in key:
                return value
        return None


CA_REGIONS = {
    "alpesprovence": "Alpes Provence",
    "alsace-vosges": "Alsace Vosges",
    "anjou-maine": "Anjou Maine",
    "aquitaine": "Aquitaine",
    "atlantique-vendee": "Atlantique Vendée",
    "briepicardie": "Brie Picardie",
    "centrest": "Centre Est",
    "centrefrance": "Centre France",
    "centreloire": "Centre Loire",
    "centreouest": "Centre Ouest",
    "cb": "Champagne Bourgogne",
    "cmds": "Charente Maritime Deux-Sèvres",
    "charente-perigord": "Charente Périgord",
    "corse": "Corse",
    "cotesdarmor": "Côtes d'Armor",
    "des-savoie": "Des Savoie",
    "finistere": "Finistère",
    "franchecomte": "Franche Comté",
    "guadeloupe": "Guadeloupe",
    "illeetvilaine": "Ille et Vilaine",
    "languedoc": "Languedoc",
    "loirehauteloire": "Loire Haute-Loire",
    "lorraine": "Lorraine",
    "martinique": "Martinique",
    "morbihan": "Morbihan",
    "norddefrance": "Nord de France",
    "nord-est": "Nord Est",
    "nmp": "Nord Midi Pyrénées",
    "normandie": "Normandie",
    "normandie-seine": "Normandie Seine",
    "paris": "Paris",
    "pca": "Provence Côte d'Azur",
    "pyrenees-gascogne": "Pyrénées Gascogne",
    "reunion": "Réunion",
    "sudmed": "Sud Méditerranée",
    "sudrhonealpes": "Sud Rhône Alpes",
    "toulouse31": "Toulouse",
    "tourainepoitou": "Touraine Poitou",
    "valdefrance": "Val de France",
}

DEPARTMENTS_TO_CA_REGIONS = {
    ('20', '2A', '2B'): ['corse'],
    ('1', '71'): ['centrest'],
    ('2', '8', '51'): ['nord-est'],
    ('4', '6', '83'): ['pca'],
    ('5', '13', '84'): ['alpesprovence'],
    ('10', '21', '52', '89'): ['cb'],
    ('11', '30', '34', '48'): ['languedoc'],
    ('12', '46', '81', '82'): ['nmp'],
    ('14', '50'): ['normandie'],
    ('53', '61'): ['normandie', 'anjou-maine'],
    ('15', '23', '63', '03', '19'): ['centrefrance'],
    ('16', '24'): ['charente-perigord'],
    ('17', '79'): ['cmds'],
    ('18', '58'): ['centreloire'],
    ('56',): ['morbihan'],
    ('45',): ['briepicardie', 'centreloire'],
    ('22',): ['cotesdarmor'],
    ('25', '39', '70', '90'): ['franchecomte'],
    ('26', '38', '69', '7'): ['centrest', 'sudrhonealpes'],
    ('27', '76'): ['normandie-seine'],
    ('28', '41'): ['valdefrance'],
    ('29',): ['finistere'],
    ('31',): ['toulouse31'],
    ('32',): ['aquitaine', 'pyrenees-gascogne'],
    ('33', '40', '47'): ['aquitaine'],
    ('35',): ['illeetvilaine'],
    ('36', '87'): ['centreouest'],
    ('37', '86'): ['tourainepoitou'],
    ('54', '55', '57'): ['lorraine'],
    ('67', '68', '88'): ['alsace-vosges'],
    ('42', '43'): ['loirehauteloire'],
    ('44', '85'): ['atlantique-vendee'],
    ('11', '30', '34', '48',): ['languedoc'],
    ('49', '72'): ['anjou-maine'],
    ('59', '62'): ['norddefrance'],
    ('64', '65'): ['pyrenees-gascogne'],
    ('66', '9'): ['sudmed'],
    ('73', '74'): ['des-savoie'],
    ('75', '91', '92', '93', '94', '95', '78'): ['paris'],
    ('60',): ['briepicardie', 'paris'],
    ('80', '77'): ['briepicardie'],
    ('971',): ['guadeloupe'],
    ('972', '973'): ['martinique'],
    ('974',): ['reunion']
}
