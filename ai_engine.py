# =====================================================
# ai_engine.py
# =====================================================


def generate_ai_signal(
    spot_price,
    previous_spot,
    total_pcr,
    total_ce_oi,
    total_pe_oi,
    atm_ce_volume,
    atm_pe_volume,
):

    # =================================================
    # PRICE TREND
    # =================================================
    bullish_price = spot_price > previous_spot

    bearish_price = spot_price < previous_spot
# =================================================
    # BUY CALL
    # =================================================
    if (
        total_pcr > 1
        and total_pe_oi > total_ce_oi
        and bullish_price
        and atm_ce_volume > atm_pe_volume
    ):

        return {
            "signal": "BUY CALL",
            "confidence": "HIGH",
            "color": "green",
        }
# =================================================
    # BUY PUT
    # =================================================
    elif (
        total_pcr < 0.8
        and total_ce_oi > total_pe_oi
        and bearish_price
        and atm_pe_volume > atm_ce_volume
    ):

        return {
            "signal": "BUY PUT",
            "confidence": "HIGH",
            "color": "red",
        }

    # =================================================
    # NO TRADE
    # =================================================
    else:

        return {
            "signal": "NO TRADE",
            "confidence": "LOW",
            "color": "gray",
        }