"""
VOID Tools — Social Scraper
Returns public social profile viewer tools and generates direct profile URLs.
GET /api/social-scraper?username=johndoe&platform=instagram&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json

LABELS = {
    "en":{"tool":"Social Scraper","error":"Error",
          "note":"All tools listed access only public profile data. Respect platform ToS."},
    "fr":{"tool":"Scraper Social","error":"Erreur",
          "note":"Tous les outils listés accèdent uniquement aux données publiques. Respectez les CGU des plateformes."},
}

TOOLS = [
    {"name":"Imginn (Instagram)","url":"https://imginn.com/","platform":"instagram","desc":"Public Instagram viewer"},
    {"name":"Exolyt (TikTok)",   "url":"https://exolyt.com/","platform":"tiktok",   "desc":"TikTok analytics"},
    {"name":"Facebook Lookup ID","url":"https://lookup-id.com/","platform":"facebook","desc":"Find Facebook numeric ID"},
    {"name":"OSINT.support",     "url":"https://osint.support/","platform":"linkedin","desc":"LinkedIn OSINT tools"},
    {"name":"SocialSearcher",    "url":"https://socialsearcher.com/","platform":"all","desc":"Cross-platform search"},
    {"name":"Sherlock",          "url":"https://sherlock-project.github.io/","platform":"all","desc":"Username hunt CLI"},
    {"name":"WhoPostedWhat",     "url":"https://whopostedwhat.com/","platform":"facebook","desc":"Facebook post search"},
    {"name":"IntelligenceX",     "url":"https://intelx.io/","platform":"all","desc":"Deep search across platforms"},
    {"name":"Social-Searcher",   "url":"https://www.social-searcher.com/","platform":"all","desc":"Real-time social monitoring"},
    {"name":"Tweetdeck",         "url":"https://tweetdeck.twitter.com/","platform":"twitter","desc":"Advanced Twitter search"},
    {"name":"Snapchat Map",      "url":"https://map.snapchat.com/","platform":"snapchat","desc":"Public Snap Map"},
    {"name":"Pimeyes",           "url":"https://pimeyes.com/","platform":"all","desc":"Reverse face image search"},
]

PLATFORM_URLS = {
    "instagram": "https://www.instagram.com/{}/",
    "twitter":   "https://x.com/{}",
    "tiktok":    "https://www.tiktok.com/@{}",
    "facebook":  "https://www.facebook.com/{}",
    "youtube":   "https://www.youtube.com/@{}",
    "linkedin":  "https://www.linkedin.com/in/{}",
    "snapchat":  "https://www.snapchat.com/add/{}",
    "reddit":    "https://www.reddit.com/user/{}",
    "twitch":    "https://www.twitch.tv/{}",
    "pinterest": "https://www.pinterest.com/{}",
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); params = parse_qs(parsed.query)
        lang = params.get("lang",["en"])[0].lower()
        if lang not in LABELS: lang = "en"
        L = LABELS[lang]
        username = params.get("username",[""])[0].strip()
        platform = params.get("platform",["all"])[0].lower()

        def send(status, payload):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)

        filtered_tools = [t for t in TOOLS if platform=="all" or t["platform"]==platform or t["platform"]=="all"]
        profile_url = None
        if username and platform in PLATFORM_URLS:
            profile_url = PLATFORM_URLS[platform].format(quote(username,safe=""))

        send(200,{"tool":L["tool"],"success":True,"lang":lang,"note":L["note"],
                  "username":username or None,"platform":platform,
                  "direct_profile_url":profile_url,
                  "profile_urls":{p:u.format(quote(username,safe="")) for p,u in PLATFORM_URLS.items()} if username else {},
                  "tools":filtered_tools,"available_platforms":list(PLATFORM_URLS.keys())})

    def log_message(self, *args): pass
