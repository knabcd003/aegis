import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from api.services.user_profile import UserProfileService

svc = UserProfileService()

for external_service, env_var in [
    ("finnhub",     "FINNHUB_API_KEY"),
    ("alpaca_key",  "ALPACA_API_KEY"),
    ("alpaca_secret", "ALPACA_SECRET_KEY"),
    ("fred",        "FRED_API_KEY"),
    ("sec_edgar",   "SEC_EDGAR_EMAIL"),
]:
    key = os.getenv(env_var)
    if key:
        svc.set_api_key("default", external_service, key)
        print(f"Seeded {external_service}")

print("Done re-seeding keys.")
