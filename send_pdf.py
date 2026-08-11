import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"

with open("custom-resume.pdf", "rb") as pdf:

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "caption": "📄 Custom Resume"
        },
        files={
            "document": (
                "custom-resume.pdf",
                pdf,
                "application/pdf"
            )
        },
        timeout=60
    )

if not response.ok:
    raise RuntimeError(
        f"Telegram error {response.status_code}: "
        f"{response.text}"
    )

print("PDF sent successfully.")
