from datetime import datetime, timedelta

from creditagricole_particuliers import Authenticator, Accounts
from constant import *
import urllib.parse
import requests


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
        self.session = requests.Session()
        print("Debug: Entering CreditAgricoleClient initialization")

        self.department = self.config.get('CreditAgricole', 'department')
        print(f"Debug: Department value: '{self.department}'")

        # Conversion du département en région
        department_to_region = {
            '31': 'toulouse31',
            # Ajoutez d'autres correspondances si nécessaire
        }

        self.region = department_to_region.get(self.department)
        if not self.region:
            print(f"Debug: Available regions: {list(CA_REGIONS.keys())}")
            self.logger.error(f"Invalid department: {self.department}")
            raise ValueError(f"Invalid department: {self.department}. Please use a valid region code.")

        print(f"Debug: Region determined: '{self.region}'")

        if self.region not in CA_REGIONS:
            self.logger.error(f"Invalid region: {self.region}")
            raise ValueError(f"Invalid region: {self.region}")

        self.username = self.config.get('CreditAgricole', 'username')
        self.password = self.config.get('CreditAgricole', 'password')

        if not self.username or not self.password:
            self.logger.error("Missing username or password")
            raise ValueError("Missing username or password")

        self.url = f"https://www.{self.region}.credit-agricole.fr"
        self.csrf_token = None

        print("Debug: CreditAgricoleClient initialization completed successfully")

    def validate(self):
        print("Debug: Entering validate method")
        
        # Vérification du nom d'utilisateur
        if not self.username:
            self.logger.error("Please set your bank account username.")
            raise ValueError("Please set your bank account username.")

        # Vérification du mot de passe
        if not self.password:
            self.logger.error("Please set your bank account password.")
            raise ValueError("Please set your bank account password.")

        print("Debug: Validation completed successfully")

    def init_session(self):
        print("Debug: Entering init_session method")
        
        password_list = []
        for char in self.password:
            if char.isdigit():
                password_list.append(int(char))
            else:
                password_list.append(ord(char))
        print(f"Debug: Password processed, length: {len(password_list)}")

        data = {
            "j_password": password_list,
            "j_username": self.username,
            "j_numeric_grid_selection": "true"
        }

        print("Debug: Preparing to send login request")
        response = self.session.post(
            f"{self.url}/particulier/acceder-a-mes-comptes.html",
            json=data
        )
        print(f"Debug: Login request sent, status code: {response.status_code}")

        if response.status_code != 200:
            error_msg = f"Login failed with status code: {response.status_code}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        print("Debug: Checking for successful login")
        if "Votre identification a échoué" in response.text:
            error_msg = "Login failed: Invalid credentials"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        print("Debug: Login successful, extracting CSRF token")
        csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        if not csrf_token:
            error_msg = "Failed to extract CSRF token"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        self.csrf_token = csrf_token.group(1)
        print(f"Debug: CSRF token extracted: {self.csrf_token[:10]}...")  # Affiche les 10 premiers caractères pour la sécurité

        print("Debug: init_session completed successfully")

    def get_accounts(self):
        accounts = []
        for account in Accounts(session=self.session):
            if account.numeroCompte in [x.strip() for x in self.enabled_accounts.split(",")]:
                accounts.append(account)
        return accounts

    def get_transactions(self, account_id):
        account = Accounts(session=self.session).search(num=account_id)

        current_date = datetime.today()
        previous_date = current_date - timedelta(days=int(self.get_transactions_period))
        date_stop_ = current_date.strftime('%Y-%m-%d')
        date_start_ = previous_date.strftime('%Y-%m-%d')

        return [op.descr for op in account.get_operations(count=int(self.max_transactions), date_start=date_start_, date_stop=date_stop_)]


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
