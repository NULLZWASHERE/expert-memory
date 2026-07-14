from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

LABELS = {
    "en": {"title": "Discord User Lookup", "error": "id parameter required (?id=...) and optional &bot_token=..."},
    "fr": {"title": "Recherche Utilisateur Discord", "error": "Paramètre id requis (?id=...) et &bot_token= optionnel"}
}

FLAGS = {
    1: "Discord Employee", 2: "Partnered Server Owner", 4: "HypeSquad Events",
    8: "Bug Hunter Lvl1", 64: "HypeSquad Bravery", 128: "HypeSquad Brilliance",
    256: "HypeSquad Balance", 512: "Early Supporter", 16384: "Bug Hunter Lvl2",
    131072: "Verified Bot Developer", 4194304: "Active Developer"
}

DISCORD_EPOCH = 1420070400000

def snowflake_to_ts(sf):
    import time
    ts = ((int(sf) >> 22) + DISCORD_EPOCH) / 1000
    return time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(ts))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        if lang not in LABELS: lang = 'en'
        L = LABELS[lang]

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        user_id = qs.get('id', [''])[0].strip()
        bot_token = qs.get('bot_token', [''])[0].strip()

        if not user_id:
            self.wfile.write(json.dumps({"error": L["error"]}).encode())
            return

        headers = {'User-Agent': 'DiscordBot (void-tools, 1.0)'}
        if bot_token:
            headers['Authorization'] = f'Bot {bot_token}'

        req = urllib.request.Request(
            f'https://discord.com/api/v10/users/{user_id}',
            headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            self.wfile.write(json.dumps({"error": f"Discord API HTTP {e.code}", "detail": body}).encode())
            return
        except Exception as ex:
            self.wfile.write(json.dumps({"error": str(ex)}).encode())
            return

        raw_flags = data.get('public_flags', 0)
        badges = [name for bit, name in FLAGS.items() if raw_flags & bit]
        avatar_hash = data.get('avatar')
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{data['id']}/{avatar_hash}.{'gif' if avatar_hash and avatar_hash.startswith('a_') else 'png'}?size=512"
            if avatar_hash else
            f"https://cdn.discordapp.com/embed/avatars/{int(data.get('discriminator', 0)) % 5}.png"
        )
        banner_hash = data.get('banner')
        banner_url = (
            f"https://cdn.discordapp.com/banners/{data['id']}/{banner_hash}.{'gif' if banner_hash and banner_hash.startswith('a_') else 'png'}?size=512"
            if banner_hash else None
        )

        result = {
            "tool": L["title"],
            "id": data.get("id"),
            "username": data.get("username"),
            "global_name": data.get("global_name"),
            "discriminator": data.get("discriminator"),
            "bot": data.get("bot", False),
            "system": data.get("system", False),
            "avatar_url": avatar_url,
            "banner_url": banner_url,
            "accent_color": data.get("accent_color"),
            "badges": badges,
            "public_flags": raw_flags,
            "premium_type": {0: "None", 1: "Nitro Classic", 2: "Nitro", 3: "Nitro Basic"}.get(data.get("premium_type", 0), "Unknown"),
            "created_at": snowflake_to_ts(data["id"]),
            "note": "Bot token required for full info on non-bot users",
        }
        self.wfile.write(json.dumps(result, indent=2).encode())

    def log_message(self, *a): pass
