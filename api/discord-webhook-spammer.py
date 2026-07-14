from http.server import BaseHTTPRequestHandler
import json

INFO = {
    "tool": "Discord Webhook Spammer — Reference",
    "disclaimer": "Technical reference only. Spamming webhooks violates Discord ToS and may result in webhook deletion and account ban.",
    "what_is_a_webhook": "A webhook URL lets anyone POST messages to a Discord channel without a bot. The URL format is: https://discord.com/api/webhooks/{webhook_id}/{webhook_token}",
    "send_message_snippet": """import requests, time

WEBHOOK_URL = "https://discord.com/api/webhooks/ID/TOKEN"
MESSAGE = "Hello from void-tools!"

payload = {
    "content": MESSAGE,
    "username": "VoidBot",          # Override display name
    "avatar_url": "https://...",    # Override avatar
    "embeds": [{                    # Optional rich embed
        "title": "Embed Title",
        "description": "Embed body",
        "color": 0xFF0000
    }]
}

# Single send
r = requests.post(WEBHOOK_URL, json=payload)
print(r.status_code)  # 204 = success

# Rate limit: 30 messages per 60 seconds per webhook
""",
    "delete_webhook_snippet": """import requests
WEBHOOK_URL = "https://discord.com/api/webhooks/ID/TOKEN"
r = requests.delete(WEBHOOK_URL)
print("Deleted" if r.status_code == 204 else r.text)
""",
    "check_webhook_snippet": """import requests
WEBHOOK_URL = "https://discord.com/api/webhooks/ID/TOKEN"
r = requests.get(WEBHOOK_URL)
print(r.json())  # Returns webhook info
""",
    "rate_limits": {
        "per_webhook": "30 messages per 60 seconds",
        "global": "50 requests/second",
        "embed_fields": "Up to 25 fields per embed",
        "content_length": "2000 characters max"
    },
    "better_alternatives": [
        "Use Discord bots with proper rate limit handling",
        "Use Discord's official message scheduling for announcements",
        "Use Zapier/Make.com for automated webhook workflows"
    ]
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(INFO, indent=2).encode())

    def log_message(self, *a): pass
