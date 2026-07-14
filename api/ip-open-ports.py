"""
VOID Tools — IP Open Ports
Vercel Python Serverless Function
GET /api/ip-open-ports?ip=1.2.3.4&lang=en&timeout=1
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

IP_REGEX = re.compile(
    r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

COMMON_PORTS = {
    21:    "FTP",
    22:    "SSH",
    23:    "Telnet",
    25:    "SMTP",
    53:    "DNS",
    80:    "HTTP",
    110:   "POP3",
    143:   "IMAP",
    443:   "HTTPS",
    445:   "SMB",
    3306:  "MySQL",
    3389:  "RDP",
    5432:  "PostgreSQL",
    6379:  "Redis",
    8080:  "HTTP-alt",
    8443:  "HTTPS-alt",
    27017: "MongoDB",
}

LABELS = {
    "en": {
        "tool": "IP Open Ports",
        "missing": "Missing 'ip' query parameter. Usage: /api/ip-open-ports?ip=1.2.3.4",
        "invalid": "Invalid IP address format.",
        "error_net": "Scan error",
        "open": "open",
        "closed": "closed",
    },
    "fr": {
        "tool": "Ports Ouverts IP",
        "missing": "Paramètre 'ip' manquant. Utilisation : /api/ip-open-ports?ip=1.2.3.4",
        "invalid": "Format d'adresse IP invalide.",
        "error_net": "Erreur de scan",
        "open": "ouvert",
        "closed": "fermé",
    },
}


def scan_port(ip: str, port: int, timeout: float) -> tuple:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip, port))
        return port, result == 0
    except socket.error:
        return port, False
    finally:
        sock.close()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        lang = params.get("lang", ["en"])[0].lower()
        if lang not in LABELS:
            lang = "en"
        L = LABELS[lang]

        ip_list = params.get("ip", [])

        try:
            timeout = float(params.get("timeout", ["1"])[0])
            timeout = max(0.2, min(timeout, 5.0))
        except ValueError:
            timeout = 1.0

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
            results = []
            with ThreadPoolExecutor(max_workers=20) as ex:
                futures = {
                    ex.submit(scan_port, ip, port, timeout): (port, service)
                    for port, service in COMMON_PORTS.items()
                }
                for fut in as_completed(futures):
                    port, is_open = fut.result()
                    service = COMMON_PORTS[port]
                    results.append({
                        "port":    port,
                        "service": service,
                        "status":  L["open"] if is_open else L["closed"],
                        "open":    is_open,
                    })

            results.sort(key=lambda x: x["port"])
            open_ports   = [r for r in results if r["open"]]
            closed_ports = [r for r in results if not r["open"]]

            send(200, {
                "tool":    L["tool"],
                "success": True,
                "lang":    lang,
                "ip":      ip,
                "summary": {
                    "total":  len(results),
                    "open":   len(open_ports),
                    "closed": len(closed_ports),
                },
                "ports": results,
            })
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error_net']}: {str(e)}"})

    def log_message(self, *args):
        pass
