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
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.department = config.get('CreditAgricole', 'department')
        self.username = config.get('CreditAgricole', 'username')
        self.password = self.parse_password(config.get('CreditAgricole', 'password'))
        self.session = None

    def log_message(self, message, level=logging.INFO):
        if hasattr(self.logger, 'log'):
            self.logger.log(level, message)
        elif hasattr(self.logger, 'info'):
            self.logger.info(message)
        else:
            print(message)  # Fallback to print if no suitable logging method is found
            
    def parse_password(self, password_string):
        # Convertit la chaîne de caractères du mot de passe en liste d'entiers
        return [int(char) for char in password_string]
        
    def init_session(self):
        try:
            self.session = Authenticator(
                username=self.username,
                password=self.password,
                department=int(self.department)
            )
            self.logger.info("Session initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize session: {str(e)}")
            raise

    def validate(self):
        if not self.username or not self.password or not self.department:
            self.logger.error("Missing credentials")
            raise ValueError("Username, password, or department is missing")
        self.logger.info("Credentials validated")

    # Ajoutez d'autres méthodes selon vos besoins, par exemple :
    def get_accounts(self):
        if not self.session:
            raise ValueError("Session not initialized. Call init_session() first.")
        # Utilisez self.session pour obtenir les informations des comptes
        # Exemple (à adapter selon l'API de creditagricole_particuliers) :
        # return self.session.get_accounts()

    def get_transactions(self, account_id):
        if not self.session:
            raise ValueError("Session not initialized. Call init_session() first.")
        # Utilisez self.session pour obtenir les transactions
        # Exemple (à adapter selon l'API de creditagricole_particuliers) :
        # return self.session.get_transactions(account_id)

    def extract_csrf_token(self, html_content):
        # Try different patterns to extract CSRF token
        patterns = [
            r'name="csrf_token".*?value="([^"]+)"',
            r'data-csrf-token="([^"]+)"',
            r'csrf-token\s*:\s*["\']([^"\']+)["\']',
            r'<input[^>]*name="_csrf_token"[^>]*value="([^"]*)"',
            r'<meta name="csrf-token" content="([^"]*)"'
        ]
        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def encode_password(self):
        # This method needs to be adapted based on how the bank's virtual keypad works
        return ','.join(str(ord(char)) for char in self.password)

    def handle_additional_auth(self, response):
        # Implement SécuriPass or SMS authentication here
        # This will depend on the specific implementation of the bank
        self.logger.warning("Additional authentication not implemented")
        return False

    def get_accounts(self):
        # Implement method to fetch account information
        pass

    def get_transactions(self, account_id):
        # Implement method to fetch transactions for a specific account
        pass

    def logout(self):
        logout_url = urljoin(self.base_url, "particulier/deconnexion.html")
        self.session.get(logout_url, headers=self.headers)
        self.logger.info("Logged out successfully")

    def check_connection(self):
        try:
            response = self.session.get(self.base_url, headers=self.headers)
            return response.status_code == 200
        except requests.RequestException:
            return False

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
