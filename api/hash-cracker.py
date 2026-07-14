"""
VOID Tools — Hash Cracker & Analyzer
Identifies hash type, computes hash of any input, and provides cracking service links.
GET /api/hash-cracker?input=hello&mode=analyze&lang=en
     mode = hash (compute hash of input) | analyze (detect type + cracking links for a hash)
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json, hashlib, re

LABELS = {
    "en":{"tool":"Hash Cracker","missing":"Missing 'input'. Usage: /api/hash-cracker?input=hello&mode=hash","error":"Error",
          "mode_hash":"Hash computation","mode_analyze":"Hash analysis"},
    "fr":{"tool":"Craqueur de Hash","missing":"Paramètre 'input' manquant.","error":"Erreur",
          "mode_hash":"Calcul de hash","mode_analyze":"Analyse de hash"},
}

HASH_PATTERNS = [
    (32,  "md5",    r'^[a-f0-9]{32}$'),
    (40,  "sha1",   r'^[a-f0-9]{40}$'),
    (56,  "sha224", r'^[a-f0-9]{56}$'),
    (64,  "sha256", r'^[a-f0-9]{64}$'),
    (96,  "sha384", r'^[a-f0-9]{96}$'),
    (128, "sha512", r'^[a-f0-9]{128}$'),
    (32,  "md4",    r'^[a-f0-9]{32}$'),
    (13,  "des",    r'^[a-zA-Z0-9./]{13}$'),
]

CRACK_SERVICES = [
    ("CrackStation",  "https://crackstation.net/"),
    ("HashKiller",    "https://hashkiller.io/listmanager"),
    ("MD5Decrypt",    "https://md5decrypt.net/"),
    ("Hashes.com",    "https://hashes.com/en/decrypt/hash"),
    ("OnlineHashCrack","https://www.onlinehashcrack.com/"),
    ("CMD5",          "https://www.cmd5.org/"),
]

def identify_hash(h):
    h_lower = h.lower().strip()
    types = []
    for length, name, pattern in HASH_PATTERNS:
        if len(h_lower)==length and re.match(pattern, h_lower):
            types.append(name)
    return list(dict.fromkeys(types)) or ["unknown"]

def compute_all(text):
    b = text.encode("utf-8","replace")
    algos = ["md5","sha1","sha224","sha256","sha384","sha512","sha3_256","sha3_512","blake2b","blake2s"]
    result = {}
    for a in algos:
        try: result[a] = hashlib.new(a,b).hexdigest()
        except: pass
    return result

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); params = parse_qs(parsed.query)
        lang = params.get("lang",["en"])[0].lower()
        if lang not in LABELS: lang = "en"
        L = LABELS[lang]
        mode = params.get("mode",["hash"])[0].lower()

        def send(status, payload):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)

        inp_list = params.get("input",[])
        if not inp_list or not inp_list[0].strip(): send(400,{"tool":L["tool"],"success":False,"error":L["missing"]}); return
        inp = inp_list[0].strip()

        try:
            if mode == "hash":
                hashes = compute_all(inp)
                send(200,{"tool":L["tool"],"success":True,"lang":lang,"mode":L["mode_hash"],
                          "input":inp,"input_length":len(inp),"hashes":hashes})
            else:
                types = identify_hash(inp)
                send(200,{"tool":L["tool"],"success":True,"lang":lang,"mode":L["mode_analyze"],
                          "hash":inp,"hash_length":len(inp),
                          "detected_types":types,
                          "crack_services":[{"name":n,"url":u} for n,u in CRACK_SERVICES],
                          "note":"To crack this hash, copy it into one of the services above."})
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
