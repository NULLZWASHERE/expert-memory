from http.server import BaseHTTPRequestHandler
import json, urllib.request, re, concurrent.futures

LABELS = {
    "en": {"title": "Proxy Scraper", "note": "Scraped from public free-proxy lists. Not verified."},
    "fr": {"title": "Scraper de Proxies", "note": "Récupéré de listes publiques. Non vérifié."}
}

SOURCES = [
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "http"),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt", "socks4"),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt", "socks5"),
    ("https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt", "http"),
    ("https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt", "socks5"),
    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt", "http"),
]

IP_PORT_RE = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})')

def scrape_source(url, ptype):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            text = r.read().decode(errors='ignore')
        return [(m.group(1), m.group(2), ptype) for m in IP_PORT_RE.finditer(text)]
    except Exception:
        return []

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        if lang not in LABELS: lang = 'en'
        L = LABELS[lang]
        ptype_filter = qs.get('type', ['all'])[0].lower()
        limit = min(int(qs.get('limit', ['100'])[0]), 500)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        all_proxies = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            futures = [ex.submit(scrape_source, url, pt) for url, pt in SOURCES]
            for f in concurrent.futures.as_completed(futures):
                all_proxies.extend(f.result())

        seen = set()
        unique = []
        for ip, port, pt in all_proxies:
            key = f"{ip}:{port}"
            if key not in seen:
                seen.add(key)
                if ptype_filter == 'all' or pt == ptype_filter:
                    unique.append({"ip": ip, "port": port, "type": pt, "proxy": key})

        proxies = unique[:limit]
        self.wfile.write(json.dumps({
            "tool": L["title"],
            "note": L["note"],
            "total_scraped": len(unique),
            "returned": len(proxies),
            "filter_type": ptype_filter,
            "available_types": ["http", "socks4", "socks5"],
            "proxies": proxies,
        }, indent=2).encode())

    def log_message(self, *a): pass
