"""
VOID Tools — Username Hunter
Returns direct profile URLs for a username across 20+ platforms.
Optionally performs HTTP reachability check.
GET /api/username-hunter?username=johndoe&check=false&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 5
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

PLATFORMS = [
    ("GitHub",      "https://github.com/{}"),
    ("Twitter/X",   "https://x.com/{}"),
    ("Instagram",   "https://www.instagram.com/{}"),
    ("TikTok",      "https://www.tiktok.com/@{}"),
    ("Reddit",      "https://www.reddit.com/user/{}"),
    ("Twitch",      "https://www.twitch.tv/{}"),
    ("YouTube",     "https://www.youtube.com/@{}"),
    ("Steam",       "https://steamcommunity.com/id/{}"),
    ("Snapchat",    "https://www.snapchat.com/add/{}"),
    ("Pinterest",   "https://www.pinterest.com/{}"),
    ("Medium",      "https://medium.com/@{}"),
    ("Telegram",    "https://t.me/{}"),
    ("GitLab",      "https://gitlab.com/{}"),
    ("LinkedIn",    "https://www.linkedin.com/in/{}"),
    ("Tumblr",      "https://{}.tumblr.com"),
    ("SoundCloud",  "https://soundcloud.com/{}"),
    ("Dribbble",    "https://dribbble.com/{}"),
    ("Behance",     "https://www.behance.net/{}"),
    ("Patreon",     "https://www.patreon.com/{}"),
    ("DeviantArt",  "https://www.deviantart.com/{}"),
    ("Flickr",      "https://www.flickr.com/people/{}"),
    ("Vimeo",       "https://vimeo.com/{}"),
    ("npm",         "https://www.npmjs.com/~{}"),
    ("PyPI",        "https://pypi.org/user/{}"),
    ("DockerHub",   "https://hub.docker.com/u/{}"),
]

NOT_FOUND = ["page not found","user not found","this account doesn't exist",
             "sorry, this page isn't available","404","doesn't exist","profile not found"]

LABELS = {
    "en":{"tool":"Username Hunter","missing":"Missing 'username'. Usage: /api/username-hunter?username=johndoe",
          "error":"Error","found":"found","absent":"absent"},
    "fr":{"tool":"Chasseur de Pseudo","missing":"Paramètre 'username' manquant.",
          "error":"Erreur","found":"trouvé","absent":"absent"},
}

def probe(platform, url_tmpl, username):
    url = url_tmpl.format(username)
    req = urllib.request.Request(url, headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.status==200:
                body = r.read().decode("utf-8","replace").lower()
                for ind in NOT_FOUND:
                    if ind in body: return {"platform":platform,"url":url,"exists":False}
                return {"platform":platform,"url":url,"exists":True}
            return {"platform":platform,"url":url,"exists":False,"http_code":r.status}
    except urllib.error.HTTPError as e:
        return {"platform":platform,"url":url,"exists":e.code not in (404,410),"http_code":e.code}
    except: return {"platform":platform,"url":url,"exists":None,"error":"timeout_or_unreachable"}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); params = parse_qs(parsed.query)
        lang = params.get("lang",["en"])[0].lower()
        if lang not in LABELS: lang = "en"
        L = LABELS[lang]

        do_check = params.get("check",["false"])[0].lower() in ("true","1","yes")

        def send(status, payload):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)

        un_list = params.get("username",[])
        if not un_list or not un_list[0].strip(): send(400,{"tool":L["tool"],"success":False,"error":L["missing"]}); return
        username = un_list[0].strip()

        try:
            if do_check:
                results = []
                with ThreadPoolExecutor(max_workers=12) as ex:
                    futures = [ex.submit(probe,p,u,username) for p,u in PLATFORMS]
                    for f in as_completed(futures): results.append(f.result())
                results.sort(key=lambda x:(x["exists"] is not True, x["platform"]))
                found = [r for r in results if r["exists"] is True]
                absent = [r for r in results if r["exists"] is not True]
                send(200,{"tool":L["tool"],"success":True,"lang":lang,"username":username,
                          "summary":{"checked":len(results),"found":len(found),"absent":len(absent)},
                          "results":results})
            else:
                urls = [{"platform":p,"url":u.format(username)} for p,u in PLATFORMS]
                send(200,{"tool":L["tool"],"success":True,"lang":lang,"username":username,
                          "note":"Pass check=true to perform HTTP reachability probes.",
                          "platforms_checked":len(urls),"urls":urls})
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
