"""
VOID Tools — Email Info
DNS records (MX, SPF, DMARC, A, TXT) + Hunter.io deliverability + Gravatar check.
GET /api/email-info?email=test@gmail.com&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, re, hashlib, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 6
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
HUNTER_KEY = "432dfd7cbfec2b733603e519786b4156a789bac3"

LABELS = {
    "en":{"tool":"Email Info","missing":"Missing 'email'. Usage: /api/email-info?email=test@gmail.com","invalid":"Invalid email format.","error":"Error"},
    "fr":{"tool":"Info Email","missing":"Paramètre 'email' manquant.","invalid":"Format email invalide.","error":"Erreur"},
}

def dns_lookup(domain, rtype):
    """Use Google DNS-over-HTTPS JSON API (no dnspython needed)."""
    try:
        url = f"https://dns.google/resolve?name={domain}&type={rtype}"
        req = urllib.request.Request(url, headers={"Accept":"application/dns-json","User-Agent":"VoidTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read())
        answers = data.get("Answer",[])
        return [a.get("data","") for a in answers] if answers else None
    except: return None

def hunter_verify(email):
    try:
        url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_KEY}"
        req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"VoidTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        dd = d.get("data",{})
        return {"status":dd.get("status","unknown"),"score":dd.get("score","N/A"),"disposable":dd.get("disposable",False),"webmail":dd.get("webmail",False)}
    except: return {"status":"unavailable","score":"N/A","disposable":None,"webmail":None}

def gravatar_check(email):
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/{h}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"VoidTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        entry = d.get("entry",[{}])[0]
        return {"has_gravatar":True,"display_name":entry.get("displayName","N/A"),"profile_url":entry.get("profileUrl","N/A")}
    except urllib.error.HTTPError as e:
        return {"has_gravatar": e.code!=404,"http_code":e.code}
    except: return {"has_gravatar":False}

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

        em_list = params.get("email",[])
        if not em_list or not em_list[0].strip(): send(400,{"tool":L["tool"],"success":False,"error":L["missing"]}); return
        email = em_list[0].strip().lower()
        if not EMAIL_RE.match(email): send(400,{"tool":L["tool"],"success":False,"error":L["invalid"],"input":email}); return

        try:
            parts = email.split("@"); username = parts[0]; domain = parts[1]
            tld = "."+domain.split(".")[-1]

            with ThreadPoolExecutor(max_workers=6) as ex:
                f_mx    = ex.submit(dns_lookup, domain, "MX")
                f_spf   = ex.submit(dns_lookup, domain, "TXT")
                f_dmarc = ex.submit(dns_lookup, f"_dmarc.{domain}", "TXT")
                f_a     = ex.submit(dns_lookup, domain, "A")
                f_aaaa  = ex.submit(dns_lookup, domain, "AAAA")
                f_hunt  = ex.submit(hunter_verify, email)
                f_grav  = ex.submit(gravatar_check, email)

            spf_records = [r for r in (f_spf.result() or []) if r.startswith('"v=spf')]
            dmarc_records = [r for r in (f_dmarc.result() or []) if "DMARC" in r.upper() or "dmarc" in r.lower() or "v=DMARC" in r]
            if not dmarc_records: dmarc_records = f_dmarc.result()

            send(200,{
                "tool":L["tool"],"success":True,"lang":lang,
                "email":email,"username":username,"domain":domain,"tld":tld,
                "verification": f_hunt.result(),
                "gravatar": f_grav.result(),
                "dns": {
                    "mx": f_mx.result() or [],
                    "spf": spf_records or [],
                    "dmarc": dmarc_records or [],
                    "a": f_a.result() or [],
                    "aaaa": f_aaaa.result() or [],
                }
            })
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
