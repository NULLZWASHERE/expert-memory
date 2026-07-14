from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

LABELS = {
    "en": {"title": "Discord Invite Info", "error": "code parameter required (?code=...)"},
    "fr": {"title": "Info Invitation Discord", "error": "Paramètre code requis (?code=...)"}
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

        code = qs.get('code', [''])[0].strip()
        # Allow full invite URLs
        code = code.replace('https://discord.gg/', '').replace('https://discord.com/invite/', '').strip('/')
        if not code:
            self.wfile.write(json.dumps({"error": L["error"]}).encode())
            return

        url = f'https://discord.com/api/v10/invites/{code}?with_counts=true&with_expiration=true'
        req = urllib.request.Request(url, headers={'User-Agent': 'DiscordBot (void-tools, 1.0)'})
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

        guild = data.get('guild', {})
        channel = data.get('channel', {})
        inviter = data.get('inviter', {})

        guild_id = guild.get('id')
        icon_hash = guild.get('icon')
        icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.{'gif' if icon_hash and icon_hash.startswith('a_') else 'png'}" if icon_hash else None

        splash_hash = guild.get('splash')
        splash_url = f"https://cdn.discordapp.com/splashes/{guild_id}/{splash_hash}.png" if splash_hash else None

        banner_hash = guild.get('banner')
        banner_url = f"https://cdn.discordapp.com/banners/{guild_id}/{banner_hash}.png" if banner_hash else None

        result = {
            "tool": L["title"],
            "invite_code": code,
            "invite_url": f"https://discord.gg/{code}",
            "type": data.get("type"),
            "expires_at": data.get("expires_at"),
            "guild": {
                "id": guild_id,
                "name": guild.get("name"),
                "description": guild.get("description"),
                "created_at": snowflake_to_ts(guild_id) if guild_id else None,
                "verification_level": {0:"None",1:"Low",2:"Medium",3:"High",4:"Highest"}.get(guild.get("verification_level",0),"Unknown"),
                "nsfw_level": {0:"Default",1:"Explicit",2:"Safe",3:"Age Restricted"}.get(guild.get("nsfw_level",0),"Unknown"),
                "premium_tier": {0:"None",1:"Level 1",2:"Level 2",3:"Level 3"}.get(guild.get("premium_tier",0),"None"),
                "features": guild.get("features", []),
                "icon_url": icon_url,
                "splash_url": splash_url,
                "banner_url": banner_url,
            },
            "channel": {
                "id": channel.get("id"),
                "name": channel.get("name"),
                "type": channel.get("type"),
            },
            "inviter": {
                "id": inviter.get("id"),
                "username": inviter.get("username"),
            } if inviter else None,
            "approximate_member_count": data.get("approximate_member_count"),
            "approximate_presence_count": data.get("approximate_presence_count"),
        }
        self.wfile.write(json.dumps(result, indent=2).encode())

    def log_message(self, *a): pass
