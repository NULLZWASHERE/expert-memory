"""
VOID Tools — Name Tracker (Username OSINT)
Vercel Python Serverless Function
GET /api/name-tracker?username=johndoe&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 6

SITES = {
    "Twitter":    "https://twitter.com/{}",
    "Facebook":   "https://www.facebook.com/{}",
    "Instagram":  "https://www.instagram.com/{}",
    "GitHub":     "https://github.com/{}",
    "Reddit":     "https://www.reddit.com/user/{}",
    "LinkedIn":   "https://www.linkedin.com/in/{}",
    "Pinterest":  "https://www.pinterest.com/{}",
    "Tumblr":     "https://{}.tumblr.com",
    "YouTube":    "https://www.youtube.com/{}",
    "TikTok":     "https://www.tiktok.com/@{}",
    "Twitch":     "https://www.twitch.tv/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Medium":     "https://medium.com/@{}",
    "DeviantArt": "https://www.deviantart.com/{}",
    "Behance":    "https://www.behance.net/{}",
    "Dribbble":   "https://dribbble.com/{}",
    "Patreon":    "https://www.patreon.com/{}",
    "GitLab":     "https://gitlab.com/{}",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

NOT_FOUND_INDICATORS = [
    "page not found", "user not found", "profile not found",
    "this account doesn't exist", "sorry, this page isn't available",
    "404", "doesn't exist",
]

LABELS = {
    "en": {
        "tool": "Name Tracker",
        "missing": "Missing 'username' query parameter. Usage: /api/name-tracker?username=johndoe",
        "error": "Scan error",
        "found": "found",
        "absent": "absent",
    },
    "fr": {
        "tool": "Traqueur de Pseudo",
        "missing": "Paramètre 'username' manquant. Utilisation : /api/name-tracker?username=johndoe",
        "error": "Erreur de scan",
        "found": "trouvé",
        "absent": "absent",
    },
}


def check_username(site: str, url_template: str, username: str) -> dict:
    url = url_template.format(username)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8", errors="replace").lower()
                for indicator in NOT_FOUND_INDICATORS:
                    if indicator in body:
                        return {"site": site, "url": url, "exists": False}
                return {"site": site, "url": url, "exists": True}
            return {"site": site, "url": url, "exists": False}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"site": site, "url": url, "exists": False}
        return {"site": site, "url": url, "exists": False, "http_error": e.code}
    except Exception:
        return {"site": site, "url": url, "exists": False, "error": "timeout_or_unreachable"}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        lang = params.get("lang", ["en"])[0].lower()
        if lang not in LABELS:
            lang = "en"
        L = LABELS[lang]

        username_list = params.get("username", [])

        def send(status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        if not username_list:
            send(400, {"tool": L["tool"], "success": False, "error": L["missing"]})
            return

        username = username_list[0].strip()
        if not username:
            send(400, {"tool": L["tool"], "success": False, "error": L["missing"]})
            return

        try:
            results = []
            with ThreadPoolExecutor(max_workers=12) as executor:
                futures = {
                    executor.submit(check_username, site, url_tmpl, username): site
                    for site, url_tmpl in SITES.items()
                }
                for future in as_completed(futures):
                    results.append(future.result())

            results.sort(key=lambda x: (not x["exists"], x["site"]))
            found  = [r for r in results if r["exists"]]
            absent = [r for r in results if not r["exists"]]

            send(200, {
                "tool":     L["tool"],
                "success":  True,
                "lang":     lang,
                "username": username,
                "summary": {
                    "checked": len(results),
                    "found":   len(found),
                    "absent":  len(absent),
                },
                "results": results,
            })
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error']}: {str(e)}"})

    def log_message(self, *args):
        pass
