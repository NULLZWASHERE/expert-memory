"""
VOID Tools — IP Operator
Vercel Python Serverless Function
GET /api/ip-operator?ip=1.2.3.4&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re
import urllib.request

TIMEOUT = 8
IP_REGEX = re.compile(
    r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

LABELS = {
    "en": {
        "tool": "IP Operator",
        "missing": "Missing 'ip' query parameter. Usage: /api/ip-operator?ip=1.2.3.4",
        "invalid": "Invalid IP address format.",
        "error_api": "API returned failure",
        "error_net": "Network error",
    },
    "fr": {
        "tool": "Opérateur IP",
        "missing": "Paramètre 'ip' manquant. Utilisation : /api/ip-operator?ip=1.2.3.4",
        "invalid": "Format d'adresse IP invalide.",
        "error_api": "L'API a retourné une erreur",
        "error_net": "Erreur réseau",
    },
}

FIELDS = "status,message,isp,org,as,asname,query"


def get_operator(ip: str) -> dict:
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
            data = get_operator(ip)
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
                    "isp":          data.get("isp", "N/A"),
                    "organization": data.get("org", "N/A"),
                    "as":           data.get("as", "N/A"),
                    "as_name":      data.get("asname", "N/A"),
                }
            }
            send(200, result)
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error_net']}: {str(e)}"})

    def log_message(self, *args):
        pass
