"""
VOID Tools — IP Localisation
Vercel Python Serverless Function
GET /api/ip-localisation?ip=1.2.3.4&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re
import urllib.request
import urllib.error

TIMEOUT = 8
IP_REGEX = re.compile(
    r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

LABELS = {
    "en": {
        "tool": "IP Localisation",
        "missing": "Missing 'ip' query parameter. Usage: /api/ip-localisation?ip=1.2.3.4",
        "invalid": "Invalid IP address format.",
        "error_api": "API returned failure",
        "error_net": "Network error",
    },
    "fr": {
        "tool": "Localisation IP",
        "missing": "Paramètre 'ip' manquant. Utilisation : /api/ip-localisation?ip=1.2.3.4",
        "invalid": "Format d'adresse IP invalide.",
        "error_api": "L'API a retourné une erreur",
        "error_net": "Erreur réseau",
    },
}

FIELDS = "status,message,country,regionName,city,zip,lat,lon,isp,org,as,query"


def locate_ip(ip: str) -> dict:
    url = f"https://ip-api.com/json/{ip}?fields={FIELDS}"
    req = urllib.request.Request(url, headers={"User-Agent": "VoidTools/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        lang = params.get("lang", ["en"])[0].lower()
        if lang not in LABELS:
            lang = "en"
        L = LABELS[lang]

        ip_list = params.get("ip", [])

        def send(status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        if not ip_list:
            send(400, {"tool": L["tool"], "success": False, "error": L["missing"]})
            return

        ip = ip_list[0].strip()

        if not IP_REGEX.match(ip):
            send(400, {"tool": L["tool"], "success": False, "error": L["invalid"], "input": ip})
            return

        try:
            data = locate_ip(ip)
            if data.get("status") == "fail":
                send(400, {"tool": L["tool"], "success": False,
                           "error": f"{L['error_api']}: {data.get('message', 'Unknown')}"})
                return

            result = {
                "tool": L["tool"],
                "success": True,
                "lang": lang,
                "data": {
                    "ip":           data.get("query", "N/A"),
                    "country":      data.get("country", "N/A"),
                    "region":       data.get("regionName", "N/A"),
                    "city":         data.get("city", "N/A"),
                    "zip":          data.get("zip", "N/A"),
                    "latitude":     data.get("lat", "N/A"),
                    "longitude":    data.get("lon", "N/A"),
                    "isp":          data.get("isp", "N/A"),
                    "organization": data.get("org", "N/A"),
                    "as":           data.get("as", "N/A"),
                }
            }
            send(200, result)
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error_net']}: {str(e)}"})

    def log_message(self, *args):
        pass
