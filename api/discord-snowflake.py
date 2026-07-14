from http.server import BaseHTTPRequestHandler
import json, time

LABELS = {
    "en": {"title": "Discord Snowflake Decoder", "error": "id parameter required (?id=...)"},
    "fr": {"title": "Décodeur Snowflake Discord", "error": "Paramètre id requis (?id=...)"}
}

def decode_snowflake(sf):
    DISCORD_EPOCH = 1420070400000
    sf_int = int(sf)
    timestamp_ms = (sf_int >> 22) + DISCORD_EPOCH
    worker_id = (sf_int & 0x3E0000) >> 17
    process_id = (sf_int & 0x1F000) >> 12
    increment = sf_int & 0xFFF
    dt = time.gmtime(timestamp_ms / 1000)
    return {
        "snowflake": sf,
        "timestamp_ms": timestamp_ms,
        "created_at_utc": time.strftime('%Y-%m-%d %H:%M:%S UTC', dt),
        "unix_timestamp": timestamp_ms // 1000,
        "worker_id": worker_id,
        "process_id": process_id,
        "increment": increment,
        "age_days": int((time.time() - timestamp_ms / 1000) / 86400),
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

        sf = qs.get('id', [''])[0].strip()
        if not sf:
            self.wfile.write(json.dumps({"error": L["error"]}).encode())
            return
        try:
            result = decode_snowflake(sf)
            result["tool"] = L["title"]
            self.wfile.write(json.dumps(result, indent=2).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, *a): pass
