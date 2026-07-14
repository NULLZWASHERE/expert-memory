"""
VOID Tools — Search Database (Username / Email OSINT across public sources)
Vercel Python Serverless Function
GET /api/search-database?query=johndoe&type=username&lang=en
     type = username | email
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 6

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

USERNAME_SITES = {
    "GitHub":      "https://api.github.com/users/{}",
    "GitLab":      "https://gitlab.com/api/v4/users?username={}",
    "Reddit":      "https://www.reddit.com/user/{}/about.json",
    "Hacker News": "https://hacker-news.firebaseio.com/v0/user/{}.json",
    "npm":         "https://registry.npmjs.org/~{}",
    "PyPI":        "https://pypi.org/user/{}/",
    "Docker Hub":  "https://hub.docker.com/v2/users/{}/",
}

NOT_FOUND_INDICATORS = [
    "not_found", "does not exist", "user not found",
    "no user", "null", "[]",
]

LABELS = {
    "en": {
        "tool": "Search Database",
        "missing": "Missing 'query' parameter. Usage: /api/search-database?query=johndoe&type=username",
        "invalid_type": "Invalid 'type'. Must be 'username' or 'email'.",
        "error": "Search error",
        "found": "found",
        "absent": "absent",
        "note_email": "Direct email breach search requires HaveIBeenPwned API key. Returning public info only.",
    },
    "fr": {
        "tool": "Recherche Base de Données",
        "missing": "Paramètre 'query' manquant. Utilisation : /api/search-database?query=johndoe&type=username",
        "invalid_type": "Type invalide. Doit être 'username' ou 'email'.",
        "error": "Erreur de recherche",
        "found": "trouvé",
        "absent": "absent",
        "note_email": "La recherche de fuite d'email nécessite une clé API HaveIBeenPwned. Retour d'informations publiques uniquement.",
    },
}


def probe_url(label: str, url: str, found_indicator: str = None) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8", errors="replace")
                body_lower = body.lower()
                for indicator in NOT_FOUND_INDICATORS:
                    if indicator in body_lower and indicator != "null":
                        return {"source": label, "url": url, "exists": False}
                if body.strip() in ("null", "[]", ""):
                    return {"source": label, "url": url, "exists": False}
                return {"source": label, "url": url, "exists": True}
            return {"source": label, "url": url, "exists": False, "http_code": resp.status}
    except urllib.error.HTTPError as e:
        return {"source": label, "url": url, "exists": False, "http_code": e.code}
    except Exception:
        return {"source": label, "url": url, "exists": False, "error": "unreachable"}


def search_username(username: str) -> list:
    tasks = []
    for label, url_tmpl in USERNAME_SITES.items():
        url = url_tmpl.format(quote(username, safe=""))
        tasks.append((label, url))

    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(probe_url, label, url): label for label, url in tasks}
        for fut in as_completed(futures):
            results.append(fut.result())
    return sorted(results, key=lambda x: (not x["exists"], x["source"]))


def search_email(email: str) -> list:
    # Public gravatar check
    import hashlib
    email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
    gravatar_url = f"https://www.gravatar.com/{email_hash}.json"

    results = []
    req = urllib.request.Request(gravatar_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode())
                entry = body.get("entry", [{}])[0]
                results.append({
                    "source":      "Gravatar",
                    "url":         gravatar_url,
                    "exists":      True,
                    "display_name": entry.get("displayName", "N/A"),
                    "profile_url": entry.get("profileUrl", "N/A"),
                    "thumbnail":   entry.get("thumbnailUrl", "N/A"),
                })
    except urllib.error.HTTPError as e:
        results.append({
            "source": "Gravatar",
            "url": gravatar_url,
            "exists": False,
            "http_code": e.code,
        })
    except Exception:
        results.append({"source": "Gravatar", "url": gravatar_url, "exists": False, "error": "unreachable"})

    return results


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        lang = params.get("lang", ["en"])[0].lower()
        if lang not in LABELS:
            lang = "en"
        L = LABELS[lang]

        query_list = params.get("query", [])
        search_type = params.get("type", ["username"])[0].lower()

        def send(status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        if not query_list or not query_list[0].strip():
            send(400, {"tool": L["tool"], "success": False, "error": L["missing"]})
            return

        query = query_list[0].strip()

        if search_type not in ("username", "email"):
            send(400, {"tool": L["tool"], "success": False, "error": L["invalid_type"]})
            return

        try:
            if search_type == "username":
                results = search_username(query)
                note = None
            else:
                results = search_email(query)
                note = L["note_email"]

            found  = [r for r in results if r["exists"]]
            absent = [r for r in results if not r["exists"]]

            payload = {
                "tool":    L["tool"],
                "success": True,
                "lang":    lang,
                "query":   query,
                "type":    search_type,
                "summary": {
                    "checked": len(results),
                    "found":   len(found),
                    "absent":  len(absent),
                },
                "results": results,
            }
            if note:
                payload["note"] = note

            send(200, payload)
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error']}: {str(e)}"})

    def log_message(self, *args):
        pass
