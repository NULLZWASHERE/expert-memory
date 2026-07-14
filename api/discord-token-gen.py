from http.server import BaseHTTPRequestHandler
import json, secrets, base64, struct, time, random

LABELS = {
    "en": {"title": "Discord Test Token Generator"},
    "fr": {"title": "Générateur de Token Discord de Test"}
}

def make_fake_token():
    # Part 1: base64(fake_user_id) — 17-19 digit snowflake-like number
    DISCORD_EPOCH = 1420070400000
    now_ms = int(time.time() * 1000)
    # Create a fake snowflake: random time between 2016 and now
    fake_ts = random.randint(DISCORD_EPOCH, now_ms)
    worker = random.randint(0, 31)
    process = random.randint(0, 31)
    increment = random.randint(0, 4095)
    snowflake = ((fake_ts - DISCORD_EPOCH) << 22) | (worker << 17) | (process << 12) | increment
    user_id_str = str(snowflake).encode()
    part1 = base64.b64encode(user_id_str).decode().rstrip('=')

    # Part 2: base64 of timestamp (seconds since 2015-01-01)
    epoch2015 = 1420070400
    ts_offset = int(time.time()) - epoch2015 - random.randint(0, 86400 * 365)
    part2_bytes = struct.pack('>I', ts_offset)
    part2 = base64.b64encode(part2_bytes).decode().rstrip('=')

    # Part 3: 27-char random HMAC-like string
    part3 = secrets.token_urlsafe(27)[:27]

    return f"{part1}.{part2}.{part3}", snowflake

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        if lang not in LABELS: lang = 'en'
        L = LABELS[lang]
        count = min(int(qs.get('count', ['5'])[0]), 50)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        DISCORD_EPOCH = 1420070400000
        tokens = []
        for _ in range(count):
            token, sf = make_fake_token()
            ts_ms = ((sf >> 22) + DISCORD_EPOCH)
            import time as _time
            created = _time.strftime('%Y-%m-%d %H:%M:%S UTC', _time.gmtime(ts_ms / 1000))
            tokens.append({
                "token": token,
                "fake_user_id": str(sf),
                "account_created_at": created,
                "valid": False,
                "note": "Format-correct but NOT a real Discord token. Will fail on Discord API."
            })

        self.wfile.write(json.dumps({
            "tool": L["title"],
            "count": count,
            "disclaimer": "These tokens are format-correct but NOT real. They will return 401 Unauthorized from Discord API. For load testing token format parsers only.",
            "format_explanation": {
                "structure": "BASE64(user_id).BASE64(timestamp).HMAC_secret",
                "part1": "Base64-encoded user ID (Snowflake integer as string)",
                "part2": "Base64-encoded 4-byte big-endian timestamp (seconds since 2015-01-01)",
                "part3": "27-character HMAC secret (cryptographically random)"
            },
            "tokens": tokens,
        }, indent=2).encode())

    def log_message(self, *a): pass
