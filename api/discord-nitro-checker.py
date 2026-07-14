from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

LABELS = {
    "en": {"title": "Discord Nitro Checker", "error": "code parameter required (?code=...)"},
    "fr": {"title": "Vérificateur Nitro Discord", "error": "Paramètre code requis (?code=...)"}
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

        code = qs.get('code', [''])[0].strip()
        code = code.replace('https://discord.gift/', '').replace('https://discord.com/gifts/', '').strip('/')
        if not code:
            self.wfile.write(json.dumps({"error": L["error"], "example": "?code=ABCDEFG1234567890"}).encode())
            return

        url = f'https://discord.com/api/v10/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true'
        req = urllib.request.Request(url, headers={'User-Agent': 'DiscordBot (void-tools, 1.0)'})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                valid = True
                http_code = resp.getcode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            try:
                err_data = json.loads(body)
            except Exception:
                err_data = {}
            valid = False
            data = err_data
            http_code = e.code
        except Exception as ex:
            self.wfile.write(json.dumps({"error": str(ex)}).encode())
            return

        plan = data.get('subscription_plan', {}) or {}
        result = {
            "tool": L["title"],
            "code": code,
            "gift_url": f"https://discord.gift/{code}",
            "valid": valid,
            "http_status": http_code,
        }

        if valid:
            result["gift_type"] = {1: "Nitro", 3: "Nitro Classic", 5: "Nitro Basic"}.get(data.get("type", 0), f"Unknown ({data.get('type')})")
            result["uses"] = data.get("uses")
            result["max_uses"] = data.get("max_uses")
            result["expires_at"] = data.get("expires_at")
            result["redeemed"] = data.get("redeemed", False)
            result["batch_id"] = data.get("batch_id")
            if plan:
                result["plan"] = {
                    "name": plan.get("name"),
                    "price_cents": plan.get("price"),
                    "currency": plan.get("currency"),
                    "interval": plan.get("interval"),
                    "interval_count": plan.get("interval_count"),
                }
        else:
            result["discord_message"] = data.get("message", "Invalid or expired code")
            result["discord_code"] = data.get("code")

        self.wfile.write(json.dumps(result, indent=2).encode())

    def log_message(self, *a): pass
