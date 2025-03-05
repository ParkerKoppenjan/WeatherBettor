import requests

import settings
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Discord webhook
def send_webhook(event, message):
    color = 0x0d00ff

    if event == "Bet Placed":
        color = 0x7CFC00
    elif event == "Bet Sold":
        color = 0xFF5733
    elif event == "Bot Crashed":
        color = 0x8B0000
    elif event == "Bot Started":
        color = 0x00FF00

    body = {
        "content": "",
        "tts": "false",
        "embeds": [
            {
                "id": 652627557,
                "title": event,
                "description": message,
                "color": color,
                "fields": [],
                # Now in ISO 8601 format
                "timestamp": datetime.datetime.now().isoformat(),
            }
        ],
        "components": [],
        "actions": {},
        "username": "Weather Bettor " + settings.SELECTED_MARKET,
        "avatar_url": "https://imgs.search.brave.com/BnM4--zd-SoGCQ_L4Lzy_pPtRW0sLYZsVhKJIsy_luA/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9tZWRp/YS5pc3RvY2twaG90/by5jb20vaWQvMTU3/MzA4NTU5L3Bob3Rv/L21vbmV5LXBpbGUt/MTAwLWRvbGxhci1i/aWxscy5qcGc_cz02/MTJ4NjEyJnc9MCZr/PTIwJmM9Y3AzVFhU/V1YtN04tMnlab3Qz/SXNYZjF2MW1VV01s/RjFYelNlTkdaVVZO/UT0"
    }

    if os.environ["DISCORD_WEBHOOK_URL"]:
        response = requests.post(os.environ["DISCORD_WEBHOOK_URL"], json=body)
        if response.status_code == 204:
            print("Discord notification sent successfully.")
        else:
            print("Failed to send Discord notification.")
    else:
        print("No webhook URL provided, skipping Discord notification.")
        return