# =====================================================
# alerts.py
# =====================================================

import requests

BOT_TOKEN = "8636586562:AAFDK2uS6x8CfruT7uYWCyW43Ky8PYbezXc"

CHAT_ID = "8143210382"


def send_telegram_alert(message):

    url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
    }

    try:

        requests.post(
            url,
            data=payload
        )

    except Exception as e:

        print(
            "Telegram Alert Error:",
            e
        )