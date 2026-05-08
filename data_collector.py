# =========================================================
# PulseIQ — Cloud Data Collector
# =========================================================

import os
import json
import time
import schedule
import pytz

from datetime import datetime

from kiteconnect import KiteConnect

from kite_fetch import (
    load_instruments,
    fetch_option_chain,
)

from database import (
    initialize_database,
    save_oi_snapshot,
)

# =========================================================
# SETTINGS
# =========================================================
IST = pytz.timezone("Asia/Kolkata")

REFRESH_INTERVAL = 1

INDEXES = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
    "SENSEX",
    "BANKEX",
]

TOKEN_FILE = "tokens/token.json"

# =========================================================
# LOAD ENV VARIABLES
# =========================================================
API_KEY = os.getenv("API_KEY")

# =========================================================
# LOAD TOKEN
# =========================================================
def load_token():

    if not os.path.exists(TOKEN_FILE):

        return None

    with open(TOKEN_FILE, "r") as f:

        return json.load(f)

# =========================================================
# GET KITE
# =========================================================
def get_kite():

    kite = KiteConnect(
        api_key=API_KEY
    )

    token_data = load_token()

    if token_data:

        kite.set_access_token(
            token_data["access_token"]
        )

    return kite

# =========================================================
# MARKET HOURS
# =========================================================
def is_market_open():

    now = datetime.now(IST).time()

    return (
        datetime.strptime("09:15", "%H:%M").time()
        <= now <=
        datetime.strptime("15:30", "%H:%M").time()
    )

# =========================================================
# INITIALIZE
# =========================================================
print("=" * 60)
print(" PulseIQ Historical Data Collector ")
print("=" * 60)

initialize_database()

kite = get_kite()

print("🔄 Loading instruments...")

instruments_df = load_instruments(kite)

print(f"✅ Instruments Loaded: {len(instruments_df)}")

# =========================================================
# COLLECT DATA
# =========================================================
def collect_data():

    if not is_market_open():

        print(
            f"⏸ Market Closed "
            f"({datetime.now(IST).strftime('%H:%M:%S')} IST)"
        )

        return

    print(
        f"\n🚀 Collecting @ "
        f"{datetime.now(IST).strftime('%H:%M:%S')}"
    )

    for index_name in INDEXES:

        try:

            live_data = fetch_option_chain(

                kite=kite,

                instruments_df=instruments_df,

                index_name=index_name,

                num_strikes=5,

                manual_atm=None,
            )

            save_oi_snapshot(

                spot=live_data["spot"],

                atm=live_data["atm"],

                total_ce_oi=live_data["total_ce_oi"],

                total_pe_oi=live_data["total_pe_oi"],

                total_pcr=live_data["total_pcr"],

                index_name=index_name,
            )

            print(
                f"✅ {index_name:<12} | "
                f"Spot: {live_data['spot']:>10,.2f} | "
                f"ATM: {live_data['atm']} | "
                f"PCR: {live_data['total_pcr']}"
            )

        except Exception as e:

            print(f"❌ {index_name} Error: {e}")

# =========================================================
# START
# =========================================================
collect_data()

schedule.every(
    REFRESH_INTERVAL
).minutes.do(collect_data)

print(
    f"\n⏱ Running every "
    f"{REFRESH_INTERVAL} minute(s)"
)

print("Press CTRL+C to stop.\n")

# =========================================================
# LOOP
# =========================================================
while True:

    schedule.run_pending()

    time.sleep(5)