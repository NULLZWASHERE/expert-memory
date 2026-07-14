"""
VOID Tools — Dark Web & OSINT Links
Returns curated list of OSINT resources, dark web (Tor) addresses, and stresser links.
GET /api/dark-web-links?category=all&lang=en
     category = all | onion | osint | stresser | tracking | tools
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

LABELS = {
    "en":{"tool":"Dark Web & OSINT Links","error":"Error",
          "note":"Tor (.onion) links require the Tor Browser. Always use legally and ethically."},
    "fr":{"tool":"Liens Dark Web & OSINT","error":"Erreur",
          "note":"Les liens .onion nécessitent le Navigateur Tor. Utilisez toujours légalement et éthiquement."},
}

LINKS = [
    {"id":"01","name":"Mail2Tor",        "url":"http://mail2tor2zyjdctd.onion/",                                                    "category":"onion",    "description":"Anonymous email over Tor"},
    {"id":"02","name":"Hidden Wiki",     "url":"http://zqktlwiuavvvqqt4ybvgvi7tyo4hjl5xgfuvpdf6otjiycgwqbym2qad.onion/",          "category":"onion",    "description":"Tor directory / wiki"},
    {"id":"03","name":"ProPublica",      "url":"https://www.propub3r6espa33w.onion/",                                               "category":"onion",    "description":"Investigative journalism on Tor"},
    {"id":"04","name":"DuckDuckGo (Tor)","url":"http://3g2upl4pq6kufc4m.onion/",                                                   "category":"onion",    "description":"Privacy search engine on Tor"},
    {"id":"05","name":"SecureDrop",      "url":"https://secrdrop5wyphb5x.onion/",                                                   "category":"onion",    "description":"Whistleblower platform"},
    {"id":"06","name":"Sci-Hub",         "url":"http://scihub22266oqcxt.onion/",                                                    "category":"onion",    "description":"Academic papers"},
    {"id":"07","name":"CIA Onion",       "url":"http://ciadotgov4sjwlzihbbgxnqg3xiyrg7so2r2o3lt5wz5ypk4sxyjstad.onion/",          "category":"onion",    "description":"CIA official Tor site"},
    {"id":"08","name":"Hidden Answers",  "url":"http://answerszuvs3gg2l64e6hmnryudl5zgrmwm3vh65hzszdghblddvfiqd.onion/",          "category":"onion",    "description":"Anonymous Q&A"},
    {"id":"09","name":"IPLogger",        "url":"https://iplogger.org/",                                                             "category":"tracking", "description":"IP logger and tracker"},
    {"id":"10","name":"Grabify",         "url":"https://grabify.link/",                                                             "category":"tracking", "description":"IP grabber via short links"},
    {"id":"11","name":"Whatstheirip",    "url":"https://whatstheirip.tech/",                                                        "category":"tracking", "description":"IP tracking service"},
    {"id":"12","name":"Doxbin",          "url":"https://doxbin.net/",                                                               "category":"osint",    "description":"Dox database"},
    {"id":"13","name":"OSINT Industries","url":"https://osint.industries/",                                                         "category":"osint",    "description":"OSINT platform aggregator"},
    {"id":"14","name":"Epieos",          "url":"https://epieos.com/",                                                               "category":"osint",    "description":"Email/phone OSINT"},
    {"id":"15","name":"Nuwber",          "url":"https://nuwber.fr/",                                                                "category":"osint",    "description":"People search"},
    {"id":"16","name":"OSINT Framework", "url":"https://osintframework.com/",                                                       "category":"osint",    "description":"OSINT tools directory"},
    {"id":"17","name":"Whatsmyname",     "url":"https://whatsmyname.app/",                                                          "category":"osint",    "description":"Username search across platforms"},
    {"id":"18","name":"IPInfo",          "url":"https://ipinfo.io/",                                                                "category":"tools",    "description":"IP intelligence API"},
    {"id":"19","name":"Stresser.zone",   "url":"https://stresserai.ru/hub",                                                         "category":"stresser", "description":"Authorized stress testing"},
    {"id":"20","name":"Stresse.ru",      "url":"https://stresse.ru/",                                                               "category":"stresser", "description":"Authorized stress testing"},
    {"id":"21","name":"StarkStresser",   "url":"https://starkstresser.net/",                                                        "category":"stresser", "description":"Authorized stress testing"},
    {"id":"22","name":"DDoS.services",   "url":"https://ddos.services/",                                                            "category":"stresser", "description":"Authorized stress testing"},
    {"id":"23","name":"Torch",           "url":"http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion/",          "category":"onion",    "description":"Dark web search engine"},
    {"id":"24","name":"Dark Mixer",      "url":"http://hqfld5smkr4b4xrjcco7zotvoqhuuoehjdvoin755iytmpk4sm7cbwad.onion/",          "category":"onion",    "description":"Cryptocurrency mixer"},
    {"id":"25","name":"Onionwallet",     "url":"http://ovai7wvp4yj6jl3wbzihypbq657vpape7lggrlah4pl34utwjrpetwid.onion/",          "category":"onion",    "description":"Onion wallet service"},
    {"id":"26","name":"Spylink",         "url":"https://www.spylink.net/",                                                          "category":"tracking", "description":"Link tracker"},
    {"id":"27","name":"Danex",           "url":"http://danexio627wiswvlpt6ejyhpxl5gla5nt2tgvgm2apj2ofrgm44vbeyd.onion/",          "category":"onion",    "description":"Dark marketplace"},
    {"id":"28","name":"DataBase",        "url":"https://discord.gg/GgXq3nJ7QZ",                                                    "category":"tools",    "description":"VOID Tools Discord community"},
]

CATEGORIES = ["all","onion","osint","stresser","tracking","tools"]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); params = parse_qs(parsed.query)
        lang = params.get("lang",["en"])[0].lower()
        if lang not in LABELS: lang = "en"
        L = LABELS[lang]
        cat = params.get("category",["all"])[0].lower()
        if cat not in CATEGORIES: cat = "all"

        def send(status, payload):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)

        filtered = LINKS if cat=="all" else [l for l in LINKS if l["category"]==cat]
        cats = {}
        for l in LINKS:
            cats.setdefault(l["category"],[]).append(l)

        send(200,{"tool":L["tool"],"success":True,"lang":lang,"note":L["note"],
                  "category_filter":cat,"total":len(filtered),
                  "links":filtered,
                  "available_categories":CATEGORIES,
                  "counts_by_category":{c:len(v) for c,v in cats.items()}})

    def log_message(self, *args): pass
