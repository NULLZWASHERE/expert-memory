"""
VOID Tools — Gift Card Code Generator
Generates random strings in gift card code formats.
NOTE: Generated codes are random and will NOT work for actual redemption.
GET /api/gift-generator?platform=amazon&count=5&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, secrets

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

PLATFORMS = {
    "amazon":      {"name":"Amazon",       "blocks":[4,6,5],           "sep":"-"},
    "netflix":     {"name":"Netflix",       "blocks":[4,6,4],           "sep":"-"},
    "roblox":      {"name":"Roblox",        "blocks":[4,4,4,4],         "sep":"-"},
    "apple":       {"name":"Apple",         "blocks":[4,4,4,4],         "sep":"-"},
    "steam":       {"name":"Steam",         "blocks":[5,5,5],           "sep":"-"},
    "googleplay":  {"name":"Google Play",   "blocks":[4,4,4,4],         "sep":"-"},
    "spotify":     {"name":"Spotify",       "blocks":[4,4,4,4,4,2],     "sep":"-"},
    "xbox":        {"name":"Xbox",          "blocks":[5,5,5,5],         "sep":"-"},
    "psn":         {"name":"PlayStation",   "blocks":[4,4,4,4,4],       "sep":"-"},
    "nintendo":    {"name":"Nintendo",      "blocks":[4,4,4,4],         "sep":"-"},
    "ebay":        {"name":"eBay",          "blocks":[4,4,4,4],         "sep":"-"},
}

LABELS = {
    "en":{"tool":"Gift Card Generator",
          "note":"Generated codes are random strings in gift card format. They are NOT real codes and cannot be redeemed. For educational/format reference only.",
          "missing_platform":f"Missing 'platform'. Available: {', '.join(PLATFORMS.keys())}",
          "invalid_platform":"Invalid platform. Available: "+", ".join(PLATFORMS.keys()),
          "error_count":"Count must be between 1 and 200.","error":"Error"},
    "fr":{"tool":"Générateur de Cartes Cadeaux",
          "note":"Les codes générés sont des chaînes aléatoires au format carte cadeau. Ce ne sont PAS de vrais codes et ne peuvent pas être échangés. À titre éducatif uniquement.",
          "missing_platform":f"Paramètre 'platform' manquant. Disponible : {', '.join(PLATFORMS.keys())}",
          "invalid_platform":"Plateforme invalide. Disponible : "+", ".join(PLATFORMS.keys()),
          "error_count":"Le nombre doit être entre 1 et 200.","error":"Erreur"},
}

def make_code(blocks, sep):
    return sep.join(''.join(secrets.choice(CHARSET) for _ in range(n)) for n in blocks)

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

        plat_list = params.get("platform",[])
        if not plat_list: send(400,{"tool":L["tool"],"success":False,"error":L["missing_platform"],"available":list(PLATFORMS.keys())}); return
        plat = plat_list[0].strip().lower()
        if plat not in PLATFORMS: send(400,{"tool":L["tool"],"success":False,"error":L["invalid_platform"],"available":list(PLATFORMS.keys())}); return

        try: count = int(params.get("count",["5"])[0])
        except: count = 5
        if not (1<=count<=200): send(400,{"tool":L["tool"],"success":False,"error":L["error_count"]}); return

        try:
            cfg = PLATFORMS[plat]
            fmt = cfg["sep"].join("X"*n for n in cfg["blocks"])
            codes = [{"index":i+1,"code":make_code(cfg["blocks"],cfg["sep"])} for i in range(count)]
            send(200,{"tool":L["tool"],"success":True,"lang":lang,
                      "platform":cfg["name"],"format":fmt,"count":count,
                      "note":L["note"],"codes":codes,
                      "all_platforms":list(PLATFORMS.keys())})
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
