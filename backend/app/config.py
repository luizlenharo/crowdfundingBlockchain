import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    STELLAR_NETWORK: str = os.getenv("STELLAR_NETWORK", "testnet")
    CAMPAIGN_ACCOUNT_SECRET: str = os.getenv("CAMPAIGN_ACCOUNT_SECRET")
    DONOR_ACCOUNT_SECRET: str = os.getenv("DONOR_ACCOUNT_SECRET")

    CAMPAIGN_GOAL_XLM: float = float(os.getenv("CAMPAIGN_GOAL_XLM", "100.0"))
    CAMPAIGN_TITLE: str = os.getenv("CAMPAIGN_TITLE", "Vaquinha Comunitária")
    CAMPAIGN_DESCRIPTION: str = os.getenv(
        "CAMPAIGN_DESCRIPTION", "Ajude nosso projeto!"
    )

    API_TITLE: str = "Stellar Crowdfunding System"
    API_VERSION: str = "1.0.0"

    HORIZON_URL: str = "https://horizon-testnet.stellar.org"
    NETWORK_PASSPHRASE: str = "Test SDF Network ; September 2015"


settings = Settings()
