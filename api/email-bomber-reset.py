"""
VOID Tools — Email Bomber Reset (Email Platform Lookup)
Checks if an email is registered on major platforms via public password-reset and
signup-check endpoints (no Selenium — uses HTTP requests only).
GET /api/email-bomber-reset?email=test@gmail.com&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json, re, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 6
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

LABELS = {
    "en":{"tool":"Email Platform Lookup","missing":"Missing 'email'. Usage: /api/email-bomber-reset?email=test@gmail.com",
          "invalid":"Invalid email format.","error":"Error","note":"Checks public APIs only — no harmful actions performed."},
    "fr":{"tool":"Vérification Email Plateformes","missing":"Paramètre 'email' manquant.",
          "invalid":"Format email invalide.","error":"Erreur","note":"Vérifie les APIs publiques uniquement — aucune action nuisible."},
}

def check_github(email):
    """GitHub: use the public API to check if email is tied to any public commit."""
    url = f"https://api.github.com/search/users?q={quote(email)}+in:email"
    req = urllib.request.Request(url, headers={"User-Agent":"VoidTools/1.0","Accept":"application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        count = d.get("total_count",0)
        return {"platform":"GitHub","registered": count>0,"detail":f"{count} public user(s) found"}
    except: return {"platform":"GitHub","registered":None,"detail":"check failed"}

def check_gravatar(email):
    import hashlib
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/{h}.json"
    req = urllib.request.Request(url, headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            r.read()
        return {"platform":"Gravatar","registered":True,"detail":"Profile found"}
    except urllib.error.HTTPError as e:
        return {"platform":"Gravatar","registered":e.code!=404,"detail":f"HTTP {e.code}"}
    except: return {"platform":"Gravatar","registered":None,"detail":"check failed"}

def check_adobe(email):
    url = "https://auth.services.adobe.com/en_US/index.html#from_ims=true"
    req = urllib.request.Request(
        "https://ims-na1.adobelogin.com/ims/check_token/v1",
        data=json.dumps({"email":email}).encode(),
        headers={"Content-Type":"application/json","User-Agent":UA}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        return {"platform":"Adobe","registered": d.get("email_exists",False) or d.get("account",False),"detail":str(d)}
    except: return {"platform":"Adobe","registered":None,"detail":"check failed"}

def check_twitter_x(email):
    """Twitter/X doesn't have a public email check API — return manual note."""
    return {"platform":"Twitter/X","registered":None,"detail":"No public API — check manually at x.com"}

def check_facebook(email):
    return {"platform":"Facebook","registered":None,"detail":"No public API — check manually"}

def check_spotify(email):
    url = "https://spclient.wg.spotify.com/signup/public/v1/account"
    data = f"email={quote(email)}&platform=www"
    req = urllib.request.Request(url, data=data.encode(),
        headers={"Content-Type":"application/x-www-form-urlencoded","User-Agent":UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        return {"platform":"Spotify","registered": d.get("status")==1 and d.get("errors",{}).get("email")=="Email is already registered",
                "detail": str(d.get("errors",d.get("status","")))}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
            err = body.get("errors",{}).get("email","")
            return {"platform":"Spotify","registered":"already registered" in err.lower(),"detail":err}
        except: return {"platform":"Spotify","registered":None,"detail":f"HTTP {e.code}"}
    except: return {"platform":"Spotify","registered":None,"detail":"check failed"}

def check_protonmail(email):
    url = f"https://account.protonmail.com/api/core/v4/users/available"
    domain = email.split("@")[1] if "@" in email else ""
    req = urllib.request.Request(f"https://account.proton.me/api/users/available?Name={quote(email.split('@')[0])}",
        headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        return {"platform":"ProtonMail","registered": d.get("Code")!=1000,"detail":str(d.get("Code",""))}
    except: return {"platform":"ProtonMail","registered":None,"detail":"check failed"}

CHECKS = [check_github, check_gravatar, check_twitter_x, check_facebook, check_spotify, check_protonmail]

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
        if not EMAIL_RE.match(email): send(400,{"tool":L["tool"],"success":False,"error":L["invalid"]}); return

        try:
            results = []
            with ThreadPoolExecutor(max_workers=6) as ex:
                futures = [ex.submit(fn, email) for fn in CHECKS]
                for f in as_completed(futures): results.append(f.result())
            results.sort(key=lambda x: x["platform"])
            found = [r for r in results if r["registered"] is True]
            send(200,{"tool":L["tool"],"success":True,"lang":lang,"email":email,
                      "note":L["note"],
                      "summary":{"checked":len(results),"registered":len(found),"unknown":sum(1 for r in results if r["registered"] is None)},
                      "results":results})
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
