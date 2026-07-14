"""
VOID Tools — Nitro Generator
Generates Discord Nitro gift link format codes (random strings).
NOTE: These are NOT verified and will NOT work — for educational/format reference only.
GET /api/nitro-generator?count=5&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, secrets, string

CHARSET = string.ascii_letters + string.digits
CODE_LENGTH = 16

LABELS = {
    "en":{"tool":"Nitro Generator",
          "note":"Generated codes are random strings in Discord gift format. They are NOT verified and will NOT redeem Nitro. For educational/format reference only.",
          "error_count":"Count must be between 1 and 100.","error":"Error"},
    "fr":{"tool":"Générateur Nitro",
          "note":"Les codes générés sont des chaînes aléatoires au format cadeau Discord. Ils NE SONT PAS vérifiés et ne débloqueront PAS Nitro. À titre éducatif uniquement.",
          "error_count":"Le nombre doit être entre 1 et 100.","error":"Erreur"},
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); params = parse_qs(parsed.query)
        lang = params.get("lang",["en"])[0].lower()
        if lang not in LABELS: lang = "en"
        L = LABELS[lang]

        def send(status, payload):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)

        try: count = int(params.get("count",["5"])[0])
        except: count = 5
        if not (1<=count<=100): send(400,{"tool":L["tool"],"success":False,"error":L["error_count"]}); return

        try:
            codes = []
            for i in range(count):
                code = ''.join(secrets.choice(CHARSET) for _ in range(CODE_LENGTH))
                codes.append({"index":i+1,"code":code,"url":f"https://discord.gift/{code}"})
            send(200,{"tool":L["tool"],"success":True,"lang":lang,"count":count,"note":L["note"],"codes":codes})
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
