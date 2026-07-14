from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

LABELS = {
    "en": {"title": "Discord Webhook Info", "error": "url parameter required (?url=...)"},
    "fr": {"title": "Info Webhook Discord", "error": "Paramètre url requis (?url=...)"}
}

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

        wh_url = qs.get('url', [''])[0].strip()
        if not wh_url or 'discord.com/api/webhooks/' not in wh_url:
            self.wfile.write(json.dumps({"error": L["error"], "example": "?url=https://discord.com/api/webhooks/ID/TOKEN"}).encode())
            return

        req = urllib.request.Request(wh_url, headers={'User-Agent': 'DiscordBot (void-tools, 1.0)'})
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

        DISCORD_EPOCH = 1420070400000
        import time
        def snowflake_to_ts(sf):
            ts = ((int(sf) >> 22) + DISCORD_EPOCH) / 1000
            return time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(ts))

        wh_id = data.get('id', '')
        guild_id = data.get('guild_id', '')
        channel_id = data.get('channel_id', '')
        avatar_hash = data.get('avatar')
        avatar_url = f"https://cdn.discordapp.com/avatars/{wh_id}/{avatar_hash}.png" if avatar_hash else None

        result = {
            "tool": L["title"],
            "id": wh_id,
            "name": data.get("name"),
            "type": {1: "Incoming", 2: "Channel Follower", 3: "Application"}.get(data.get("type", 1), "Unknown"),
            "channel_id": channel_id,
            "guild_id": guild_id,
            "application_id": data.get("application_id"),
            "avatar_url": avatar_url,
            "created_at": snowflake_to_ts(wh_id) if wh_id else None,
            "url": wh_url,
            "token_present": bool(data.get("token")),
            "send_message_example": {
                "method": "POST",
                "url": wh_url,
                "body": {"content": "Hello from void-tools!", "username": "VoidBot"}
            }
        }
        self.wfile.write(json.dumps(result, indent=2).encode())

    def log_message(self, *a): pass
