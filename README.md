# /!\ DISCLAIMER /!\

This code has been modified by me and mainly serve my purpose. At the beggining it was a fork from https://github.com/kdtheory/credit-agricole-importer.git, the intend of this repo was to have the code in docker. I modify everythings and is now capable of many things.


![python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) 
![GitHub release (latest by date)](https://img.shields.io/github/v/release/kdtheory/credit-agricole-importer?color=brightgreen)
![GitHub Repo stars](https://img.shields.io/github/stars/kdtheory/credit-agricole-importer?color=yellow)
![GitHub issues](https://img.shields.io/github/issues/kdtheory/credit-agricole-importer?color=yellow)

# Credit Agricole Importer for FireflyIII

Automatic import of [Credit Agricole](https://www.credit-agricole.fr/) accounts and transactions into [FireflyIII](https://github.com/firefly-iii/firefly-iii) personal finance manager, 
made with use of [python-creditagricole-particuliers](https://github.com/dmachard/python-creditagricole-particuliers) and [Firefly-III-API-Client](https://github.com/ms32035/firefly-iii-client).
This project allows for the automatic import of banking transactions from a Crédit Agricole account into Firefly III, a personal financial management application. The project uses a **`.env`** file for configuring credentials and parameters, which are then processed by a **`generate_config.sh`** script to generate the necessary configuration files for the project.

## Features
- **Automatic transaction import**: Synchronizes banking transactions from the Crédit Agricole API to Firefly III.
- **Duplicate detection**: Checks before each import to avoid adding transactions that already exist in Firefly III.
- **Multi-account management**: Supports multiple Crédit Agricole accounts and maps them to specific accounts in Firefly III.
- **Automatic scheduling**: Executes daily at 8 AM via cron (configurable) to keep your data up to date.
- **Log anonymization**: Sensitive information such as amounts and descriptions are masked in logs to protect confidentiality.

<b>*</b>_Although these functionalities are available in the FireflyIII dashboard with [automated rules](https://docs.firefly-iii.org/how-to/firefly-iii/features/rules/), they have been integrated into credit-agricole-importer. This integration allows for the execution of these actions directly through the application, bypassing the need for the [FireflyIII](https://github.com/firefly-iii/firefly-iii) instance.

## Prerequisites

- A Crédit Agricole account with access to the Crédit Agricole Particuliers API.
- A [Firefly III](https://www.firefly-iii.org/) instance configured with a personal access token.
- Docker (optional but recommended for simplified execution).


## How to install

### 1. Clone the repository

```bash
git clone https://github.com/your-username/credit-agricole-firefly-importer.git
cd credit-agricole-firefly-importer 
```

## Create a Docker compose eg :
```
  credit-agricole-importer:
    image: kdtheory/credit-agricole-importer:latest
    container_name: ca_importer
    depends_on:
      - firefly-core
    environment:
      # FIREFLY_III_URL: http://firefly-core:8080
      FIREFLY_III_URL: https://your-firefly-instance.local
      FIREFLY_PERSONAL_ACCESS_TOKEN: your_personal_token
      CREDIT_AGRICOLE_USERNAME: your_username
      CREDIT_AGRICOLE_PASSWORD: =your_password
      CREDIT_AGRICOLE_DEPARTMENT=XX  # Department number (e.g., 31)
      ACCOUNTS_MAPPING: ${ACCOUNTS_MAPPING}
      LOGGING_LEVEL: DEBUG
    volumes:
      - ca_importer_data:/app/data
    restart: unless-stopped
```


## Docker compose environment (best to put in .env)
```
# Crédit Agricole Credentials
CREDIT_AGRICOLE_USERNAME=your_username
CREDIT_AGRICOLE_PASSWORD=your_password
CREDIT_AGRICOLE_DEPARTMENT=XX  # Department number (e.g., 31)

# Firefly III Configuration
FIREFLY_III_URL=https://your-firefly-instance.local
FIREFLY_III_PERSONAL_ACCESS_TOKEN=your_personal_token

# Other parameters
IMPORT_ACCOUNT_ID_LIST=ACCOUNT_IDS_TO_IMPORT (comma-separated)
GET_TRANSACTIONS_PERIOD_DAYS=30
MAX_TRANSACTIONS_PER_GET=300
```

## FAQ

### How can I get my FireflyIII `personal-token` ?

Use [Personal Access Token](https://docs.firefly-iii.org/how-to/firefly-iii/features/api/#personal-access-token_1) in your FireflyIII instance Profile menu.

### Are my Credit Agricole credentials safe ?

When it comes to storing your credentials in the ```config.ini``` file, it's crucial to ensure that this file is not accessible from public addresses. You should make every effort to secure your host machine as effectively as possible. **However, please note that I cannot be held responsible if someone manages to steal your credentials.** 

If any system security experts happen to come across this, please don't hesitate to initiate a discussion with me on how we can enhance our storage methods. Your insights and expertise would be greatly appreciated.

### Can anybody contribute ?

Certainly! If you have any improvement ideas or wish to implement new features yourself, please don't hesitate to do so. I'm open to pull requests, but I do take a thorough and meticulous approach when reviewing them before merging. **Your contributions are highly appreciated!** 😃

## Donate ☕

In the spirit of collaboration, this project thrives thanks to the dedicated efforts of its contributors. I encourage you to explore their profiles and acknowledge their valuable contributions. However, if you'd like to show your appreciation with a small token of support, you can buy me a coffee through the following link  [here](https://www.paypal.com/donate/?hosted_button_id=JK6FX89RB8K5Y).
