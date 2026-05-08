# =========================================================
# kite_fetch.py
# =========================================================

import pandas as pd
from datetime import datetime

# =========================================================
# INDEX CONFIG
# =========================================================
INDEX_SPOT_MAP = {
    "NIFTY":      "NSE:NIFTY 50",
    "BANKNIFTY":  "NSE:NIFTY BANK",
    "FINNIFTY":   "NSE:NIFTY FIN SERVICE",
    "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
    "SENSEX":     "BSE:SENSEX",
    "BANKEX":     "BSE:BANKEX",
}

# =========================================================
# STRIKE INTERVALS
# =========================================================
STRIKE_INTERVALS = {
    "NIFTY":      50,
    "BANKNIFTY":  100,
    "FINNIFTY":   50,
    "MIDCPNIFTY": 25,
    "SENSEX":     100,
    "BANKEX":     100,
}

# =========================================================
# LOAD INSTRUMENTS
# =========================================================
def load_instruments(kite):

    nfo = kite.instruments("NFO")

    try:
        bfo = kite.instruments("BFO")
        instruments = nfo + bfo
    except:
        instruments = nfo

    df = pd.DataFrame(instruments)

    df["expiry"] = pd.to_datetime(df["expiry"]).dt.date

    return df


# =========================================================
# ROUND TO STRIKE
# =========================================================
def round_to_strike(price, interval):

    return round(price / interval) * interval


# =========================================================
# LIVE INDEX PRICES
# =========================================================
def get_all_indices_data(kite):

    symbols = list(INDEX_SPOT_MAP.values())

    quotes = kite.quote(symbols)

    rows = []

    for index_name, symbol in INDEX_SPOT_MAP.items():

        q = quotes.get(symbol, {})

        last_price = q.get("last_price", 0)

        ohlc = q.get("ohlc", {})

        close = ohlc.get("close", last_price)

        change = round(last_price - close, 2)

        change_pct = round((change / close) * 100, 2) if close else 0

        rows.append({
            "Index": index_name,
            "Price": last_price,
            "Change": change,
            "Change %": change_pct,
        })

    return pd.DataFrame(rows)


# =========================================================
# FETCH OPTION CHAIN
# =========================================================
def fetch_option_chain(
    kite,
    instruments_df,
    index_name="NIFTY",
    num_strikes=5,
    manual_atm=None,
):

    # =====================================================
    # SPOT PRICE
    # =====================================================
    spot_symbol = INDEX_SPOT_MAP[index_name]

    spot = kite.ltp([spot_symbol])[spot_symbol]["last_price"]

    # =====================================================
    # STRIKE INTERVAL
    # =====================================================
    strike_interval = STRIKE_INTERVALS[index_name]

    # =====================================================
    # ATM STRIKE
    # =====================================================
    if manual_atm and int(manual_atm) != 0:
        atm = int(manual_atm)
    else:
        atm = round_to_strike(spot, strike_interval)

    # =====================================================
    # STRIKE LIST
    # =====================================================
    strike_list = [
        atm + (i * strike_interval)
        for i in range(-num_strikes, num_strikes + 1)
    ]

    # =====================================================
    # FILTER OPTIONS
    # =====================================================
    options_df = instruments_df[
        (instruments_df["name"] == index_name)
        & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        & (instruments_df["strike"].isin(strike_list))
    ]

    if options_df.empty:

        raise ValueError(
            f"No instruments found for {index_name}"
        )

    # =====================================================
    # NEAREST EXPIRY
    # =====================================================
    expiry = options_df["expiry"].min()

    options_df = options_df[
        options_df["expiry"] == expiry
    ]

    # =====================================================
    # QUOTE SYMBOLS
    # =====================================================
    symbols = [
        f"{row['exchange']}:{row['tradingsymbol']}"
        for _, row in options_df.iterrows()
    ]

    quotes = kite.quote(symbols)

    # =====================================================
    # BUILD OPTION CHAIN
    # =====================================================
    data = []

    total_ce_oi = 0
    total_pe_oi = 0

    for strike in strike_list:

        ce_row = options_df[
            (options_df["strike"] == strike)
            & (options_df["instrument_type"] == "CE")
        ]

        pe_row = options_df[
            (options_df["strike"] == strike)
            & (options_df["instrument_type"] == "PE")
        ]

        ce_oi = ce_ltp = 0
        pe_oi = pe_ltp = 0

        # =================================================
        # CE DATA
        # =================================================
        if not ce_row.empty:

            ce_symbol = (
                f"{ce_row.iloc[0]['exchange']}:"
                f"{ce_row.iloc[0]['tradingsymbol']}"
            )

            ce_quote = quotes.get(ce_symbol, {})

            ce_oi = ce_quote.get("oi", 0)

            ce_ltp = ce_quote.get("last_price", 0)

        # =================================================
        # PE DATA
        # =================================================
        if not pe_row.empty:

            pe_symbol = (
                f"{pe_row.iloc[0]['exchange']}:"
                f"{pe_row.iloc[0]['tradingsymbol']}"
            )

            pe_quote = quotes.get(pe_symbol, {})

            pe_oi = pe_quote.get("oi", 0)

            pe_ltp = pe_quote.get("last_price", 0)

        total_ce_oi += ce_oi
        total_pe_oi += pe_oi

        pcr = round(pe_oi / ce_oi, 3) if ce_oi != 0 else 0

        data.append({
            "Strike": strike,
            "CE_OI": ce_oi,
            "CE_LTP": ce_ltp,
            "PE_OI": pe_oi,
            "PE_LTP": pe_ltp,
            "PCR": pcr,
        })

    df = pd.DataFrame(data)

    total_pcr = (
        round(total_pe_oi / total_ce_oi, 3)
        if total_ce_oi != 0
        else 0
    )

    return {
        "spot": spot,
        "atm": atm,
        "expiry": expiry,
        "data": df,
        "total_ce_oi": total_ce_oi,
        "total_pe_oi": total_pe_oi,
        "total_pcr": total_pcr,
        "timestamp": datetime.now(),
        "index_name": index_name,
    }