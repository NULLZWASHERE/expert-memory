from http.server import BaseHTTPRequestHandler
import json, base64, urllib.request, urllib.error, time

LABELS = {
    "en": {
        "title": "Discord Token Info",
        "error": "Token parameter required (?token=...)",
        "invalid_format": "Invalid token format",
        "api_error": "Discord API error",
        "decode_failed": "Token decode failed",
    },
    "fr": {
        "title": "Info Token Discord",
        "error": "Paramètre token requis (?token=...)",
        "invalid_format": "Format de token invalide",
        "api_error": "Erreur API Discord",
        "decode_failed": "Décodage du token échoué",
    }
}

def decode_snowflake(snowflake_int):
    discord_epoch = 1420070400000
    ts = ((snowflake_int >> 22) + discord_epoch) / 1000
    return time.strftime('%Y-%m-%d %Human:%M:%S UTC', time.gmtime(ts)).replace('Human', '%H')

def decode_token(token):
    parts = token.strip().split('.')
    if len(parts) != 3:
        return None, "Not a valid 3-part token"
    try:
        padded = parts[0] + '=' * (-len(parts[0]) % 4)
        user_id_bytes = base64.b64decode(padded)
        user_id = user_id_bytes.decode('utf-8')
        created_at = None
        try:
            created_at = decode_snowflake(int(user_id))
        except Exception:
            pass
        return {"user_id": user_id, "created_at": created_at}, None
    except Exception as e:
        return None, str(e)

def check_discord_api(token):
    req = urllib.request.Request(
        'https://discord.com/api/v10/users/@me',
        headers={'Authorization': token, 'User-Agent': 'DiscordBot'}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as ex:
        return None, str(ex)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        if lang not in LABELS: lang = 'en'
        L = LABELS[lang]
        token = qs.get('token', [''])[0].strip()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not token:
            self.wfile.write(json.dumps({"error": L["error"]}).encode())
            return

        decoded, err = decode_token(token)
        if err:
            self.wfile.write(json.dumps({"error": L["invalid_format"], "detail": err}).encode())
            return

        user_data, api_err = check_discord_api(token)

        flags_map = {
            1: "Discord Employee", 2: "Partnered Server Owner", 4: "HypeSquad Events",
            8: "Bug Hunter Lvl1", 64: "HypeSquad Bravery", 128: "HypeSquad Brilliance",
            256: "HypeSquad Balance", 512: "Early Supporter", 16384: "Bug Hunter Lvl2",
            131072: "Verified Bot Developer", 4194304: "Active Developer"
        }

        result = {
            "tool": L["title"],
            "token_decoded": decoded,
            "valid": user_data is not None,
        }

        if user_data:
            raw_flags = user_data.get('public_flags', 0)
            badges = [name for bit, name in flags_map.items() if raw_flags & bit]
            result["account"] = {
                "id": user_data.get("id"),
                "username": user_data.get("username"),
                "global_name": user_data.get("global_name"),
                "discriminator": user_data.get("discriminator"),
                "email": user_data.get("email"),
                "verified": user_data.get("verified"),
                "mfa_enabled": user_data.get("mfa_enabled"),
                "locale": user_data.get("locale"),
                "premium_type": {0: "None", 1: "Nitro Classic", 2: "Nitro", 3: "Nitro Basic"}.get(user_data.get("premium_type", 0), "Unknown"),
                "flags_raw": raw_flags,
                "badges": badges,
                "avatar_url": f"https://cdn.discordapp.com/avatars/{user_data.get('id')}/{user_data.get('avatar')}.png" if user_data.get('avatar') else None,
            }
        else:
            result["api_error"] = api_err

        self.wfile.write(json.dumps(result, indent=2).encode())

    def log_message(self, *a): pass
