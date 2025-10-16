from fastapi import Request

TOKEN = "7554480933:AAESR3boR9NapytAl_dNkiMrYIXrh2doUm4"
WEBHOOK_URL = "https://workflow.pgas.ph:8080/webhook"

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
response = Request.get(url)

if response.status_code == 200:
    print("Webhook set successfully")
else:
    print("Failed to set webhook")