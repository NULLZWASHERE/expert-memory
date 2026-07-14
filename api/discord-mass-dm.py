from http.server import BaseHTTPRequestHandler
import json

LABELS = {
    "en": {"title": "Discord Mass DM — Reference"},
    "fr": {"title": "Discord Mass DM — Référence"}
}

INFO = {
    "tool": "Discord Mass DM — Reference",
    "disclaimer": "This endpoint is a technical reference only. Mass DMing users violates Discord ToS (https://discord.com/terms). Use only on accounts you own, in test environments with consent.",
    "how_it_works": [
        "1. Authenticate with a user token (not a bot token — bots cannot DM strangers)",
        "2. Scrape member list from a guild via GET /guilds/{id}/members",
        "3. Open a DM channel for each user via POST /users/@me/channels",
        "4. Send a message via POST /channels/{dm_channel_id}/messages",
        "5. Respect rate limits: 50 req/s global, 5 req/s per route",
    ],
    "python_snippet": """import requests, time

TOKEN = "YOUR_USER_TOKEN"
GUILD_ID = "GUILD_ID"
MESSAGE = "Hello!"

headers = {"Authorization": TOKEN, "Content-Type": "application/json"}

# 1. Scrape members
members = requests.get(
    f"https://discord.com/api/v10/guilds/{GUILD_ID}/members?limit=1000",
    headers=headers
).json()

for member in members:
    user = member.get("user", {})
    if user.get("bot"):
        continue
    uid = user["id"]
    # 2. Open DM
    dm = requests.post(
        "https://discord.com/api/v10/users/@me/channels",
        headers=headers,
        json={"recipient_id": uid}
    ).json()
    channel_id = dm.get("id")
    if not channel_id:
        continue
    # 3. Send message
    requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers=headers,
        json={"content": MESSAGE}
    )
    time.sleep(1.2)  # Avoid rate limit
""",
    "rate_limits": {
        "global": "50 requests/second",
        "per_route": "5 requests/second",
        "dm_limit": "Discord silently drops DMs if you exceed ~100/hour on an account",
        "ban_risk": "Very high — accounts get suspended quickly for mass DM"
    },
    "alternatives": {
        "bots": "Use a Discord bot with opt-in command to DM users",
        "announcements": "Use guild announcement channels or forum posts",
        "webhooks": "Post in channels via webhooks"
    }
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(INFO, indent=2).encode())

    def log_message(self, *a): pass
