import pandas as pd
from datetime import datetime
# =====================================================
# LOAD INSTRUMENTS
# =====================================================

def load_instruments(kite):

    instruments = kite.instruments("NFO")

    instruments_df = pd.DataFrame(instruments)

    return instruments_df

# =====================================================
# FETCH OPTION CHAIN
# =====================================================

def fetch_option_chain(
    kite,
    instruments,
    selected_index="NIFTY",
    strike_range=5,
    custom_atm=0
):

    try:

        # =====================================================
        # FILTER OPTIONS
        # =====================================================

        options_df = instruments[
            (instruments["name"] == selected_index)
            &
            (instruments["instrument_type"].isin(["CE", "PE"]))
        ].copy()

        if options_df.empty:
            raise Exception(
                f"No instruments found for {selected_index}"
            )

        # =====================================================
        # EXPIRY CLEANING
        # =====================================================

        options_df["expiry"] = pd.to_datetime(
            options_df["expiry"]
        ).dt.date

        today = datetime.now().date()

        future_expiries = options_df[
            options_df["expiry"] >= today
        ]

        if future_expiries.empty:
            raise Exception(
                f"No future expiry found for {selected_index}"
            )

        nearest_expiry = future_expiries[
            "expiry"
        ].min()

        options_df = future_expiries[
            future_expiries["expiry"] == nearest_expiry
        ]

        # =====================================================
        # SPOT SYMBOL MAP
        # =====================================================

        spot_map = {
            "NIFTY": "NSE:NIFTY 50",
            "BANKNIFTY": "NSE:NIFTY BANK",
            "FINNIFTY": "NSE:NIFTY FIN SERVICE",
            "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
        }

        spot_symbol = spot_map.get(
            selected_index,
            "NSE:NIFTY 50"
        )

        # =====================================================
        # GET SPOT PRICE
        # =====================================================

        spot_price = kite.ltp(
            [spot_symbol]
        )[spot_symbol]["last_price"]

        # =====================================================
        # ATM STRIKE
        # =====================================================

        available_strikes = sorted(
            options_df["strike"].unique()
        )

        if custom_atm != 0:
            atm_strike = custom_atm
        else:
            atm_strike = min(
                available_strikes,
                key=lambda x: abs(x - spot_price)
            )

        # =====================================================
        # STRIKE RANGE
        # =====================================================

        strike_index = available_strikes.index(
            atm_strike
        )

        start_idx = max(
            0,
            strike_index - strike_range
        )

        end_idx = min(
            len(available_strikes),
            strike_index + strike_range + 1
        )

        selected_strikes = available_strikes[
            start_idx:end_idx
        ]

        chain_df = options_df[
            options_df["strike"].isin(
                selected_strikes
            )
        ].copy()

        # =====================================================
        # TRADING SYMBOLS
        # =====================================================

        trading_symbols = []

        for _, row in chain_df.iterrows():

            trading_symbols.append(
                f"NFO:{row['tradingsymbol']}"
            )

        quotes = kite.quote(trading_symbols)

        # =====================================================
        # BUILD DATA
        # =====================================================

        final_data = []

        for strike in selected_strikes:

            ce_row = chain_df[
                (chain_df["strike"] == strike)
                &
                (chain_df["instrument_type"] == "CE")
            ]

            pe_row = chain_df[
                (chain_df["strike"] == strike)
                &
                (chain_df["instrument_type"] == "PE")
            ]

            ce_data = {}
            pe_data = {}

            # =====================================================
            # CE DATA
            # =====================================================

            if not ce_row.empty:

                ce_symbol = (
                    "NFO:"
                    +
                    ce_row.iloc[0]["tradingsymbol"]
                )

                ce_quote = quotes.get(
                    ce_symbol,
                    {}
                )

                ce_data = {
                    "CE_OI": ce_quote.get("oi", 0),
                    "CE_LTP": ce_quote.get(
                        "last_price",
                        0
                    ),
                    "CE_VOLUME": ce_quote.get(
                        "volume",
                        0
                    ),
                }

            # =====================================================
            # PE DATA
            # =====================================================

            if not pe_row.empty:

                pe_symbol = (
                    "NFO:"
                    +
                    pe_row.iloc[0]["tradingsymbol"]
                )

                pe_quote = quotes.get(
                    pe_symbol,
                    {}
                )

                pe_data = {
                    "PE_OI": pe_quote.get("oi", 0),
                    "PE_LTP": pe_quote.get(
                        "last_price",
                        0
                    ),
                    "PE_VOLUME": pe_quote.get(
                        "volume",
                        0
                    ),
                }

            # =====================================================
            # FINAL ROW
            # =====================================================

            final_data.append({

                "Strike": strike,

                "CE_OI": ce_data.get(
                    "CE_OI",
                    0
                ),

                "CE_LTP": ce_data.get(
                    "CE_LTP",
                    0
                ),

                "CE_VOLUME": ce_data.get(
                    "CE_VOLUME",
                    0
                ),

                "PE_OI": pe_data.get(
                    "PE_OI",
                    0
                ),

                "PE_LTP": pe_data.get(
                    "PE_LTP",
                    0
                ),

                "PE_VOLUME": pe_data.get(
                    "PE_VOLUME",
                    0
                ),
            })

        # =====================================================
        # RETURN
        # =====================================================

        final_df = pd.DataFrame(final_data)

        return (
            final_df,
            spot_price,
            atm_strike,
            nearest_expiry
        )

    except Exception as e:

        raise Exception(str(e))