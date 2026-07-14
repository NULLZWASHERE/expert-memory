"""
VOID Tools — IP Generator
Generates random public (non-private) IPv4 addresses.
GET /api/ip-generator?count=10&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, random

PRIVATE_RANGES = [
    (10,0,0,0,8),(172,16,0,0,12),(192,168,0,0,16),
    (127,0,0,0,8),(169,254,0,0,16),(0,0,0,0,8),(255,255,255,255,32),
]

LABELS = {
    "en":{"tool":"IP Generator","error_count":"Count must be between 1 and 500.","error":"Error"},
    "fr":{"tool":"Générateur IP","error_count":"Le nombre doit être entre 1 et 500.","error":"Erreur"},
}

def is_private(a,b,c,d):
    ip_int = (a<<24)|(b<<16)|(c<<8)|d
    for ra,rb,rc,rd,mask in PRIVATE_RANGES:
        net = (ra<<24)|(rb<<16)|(rc<<8)|rd
        m = (0xFFFFFFFF<<(32-mask))&0xFFFFFFFF
        if (ip_int&m)==(net&m): return True
    return False

def gen_public_ip():
    for _ in range(1000):
        a,b,c,d = random.randint(1,254),random.randint(0,255),random.randint(0,255),random.randint(1,254)
        if not is_private(a,b,c,d): return f"{a}.{b}.{c}.{d}"
    return "8.8.8.8"

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

        try: count = int(params.get("count",["10"])[0])
        except: count = 10
        if not (1<=count<=500): send(400,{"tool":L["tool"],"success":False,"error":L["error_count"]}); return

        try:
            ips = [gen_public_ip() for _ in range(count)]
            send(200,{"tool":L["tool"],"success":True,"lang":lang,"count":count,
                      "ips":[{"index":i+1,"ip":ip} for i,ip in enumerate(ips)]})
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
