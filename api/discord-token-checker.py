"""
VOID Tools — Discord Token Checker
Validates a Discord user token via the Discord API.
GET /api/discord-token-checker?token=YOUR_TOKEN&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, urllib.request, urllib.error

TIMEOUT = 5

LABELS = {
    "en":{"tool":"Discord Token Checker","missing":"Missing 'token'. Usage: /api/discord-token-checker?token=...","valid":"Token is VALID","invalid":"Token is INVALID or network error","error":"Error",
          "warning":"Only use tokens you own. Using others' tokens without consent is illegal."},
    "fr":{"tool":"Vérificateur de Token Discord","missing":"Paramètre 'token' manquant.","valid":"Token VALIDE","invalid":"Token INVALIDE ou erreur réseau","error":"Erreur",
          "warning":"Utilisez uniquement vos propres tokens. L'utilisation de tokens tiers sans consentement est illégale."},
}

NITRO_TYPES = {0:"None",1:"Nitro Classic",2:"Nitro",3:"Nitro Basic"}

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

        tok_list = params.get("token",[])
        if not tok_list or not tok_list[0].strip(): send(400,{"tool":L["tool"],"success":False,"error":L["missing"]}); return
        token = tok_list[0].strip()

        try:
            req = urllib.request.Request(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization":token,"User-Agent":"VoidTools/1.0"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                d = json.loads(r.read())
            discriminator = d.get("discriminator","0")
            tag = f"{d.get('username','?')}{'#'+discriminator if discriminator!='0' else ''}"
            send(200,{
                "tool":L["tool"],"success":True,"lang":lang,
                "warning":L["warning"],
                "valid":True,"status":L["valid"],
                "user":{
                    "id":d.get("id","N/A"),"username":d.get("username","N/A"),
                    "tag":tag,"email":d.get("email","hidden"),
                    "verified":d.get("verified",False),"mfa_enabled":d.get("mfa_enabled",False),
                    "nitro":NITRO_TYPES.get(d.get("premium_type",0),"Unknown"),
                    "has_phone":bool(d.get("phone")),
                    "locale":d.get("locale","N/A"),"flags":d.get("flags",0),
                }
            })
        except urllib.error.HTTPError as e:
            send(200,{"tool":L["tool"],"success":True,"lang":lang,"valid":False,"status":L["invalid"],"http_code":e.code,"warning":L["warning"]})
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
