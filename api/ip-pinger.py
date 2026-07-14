"""
VOID Tools — IP Pinger
Vercel Python Serverless Function
GET /api/ip-pinger?ip=1.2.3.4&count=4&lang=en

Note: ICMP ping is not available in serverless environments.
      This function uses a TCP connect check on port 80 and 443 as a reachability probe.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re
import socket
import time

IP_REGEX = re.compile(
    r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

PROBE_PORTS = [80, 443, 22, 21, 53]

LABELS = {
    "en": {
        "tool": "IP Pinger",
        "missing": "Missing 'ip' query parameter. Usage: /api/ip-pinger?ip=1.2.3.4",
        "invalid": "Invalid IP address format.",
        "note": "ICMP ping is unavailable in serverless. TCP probe used (ports 80,443,22,21,53).",
        "reachable": "Host appears reachable",
        "unreachable": "Host appears unreachable or all probed ports are closed",
        "error_net": "Probe error",
    },
    "fr": {
        "tool": "Ping IP",
        "missing": "Paramètre 'ip' manquant. Utilisation : /api/ip-pinger?ip=1.2.3.4",
        "invalid": "Format d'adresse IP invalide.",
        "note": "Le ping ICMP n'est pas disponible en mode serverless. Sonde TCP utilisée (ports 80,443,22,21,53).",
        "reachable": "L'hôte semble joignable",
        "unreachable": "L'hôte semble inaccessible ou tous les ports sondés sont fermés",
        "error_net": "Erreur de sonde",
    },
}


def tcp_probe(ip: str, port: int, timeout: float = 2.0) -> dict:
    start = time.time()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip, port))
        elapsed_ms = round((time.time() - start) * 1000, 2)
        return {"port": port, "open": result == 0, "latency_ms": elapsed_ms}
    except socket.error as e:
        elapsed_ms = round((time.time() - start) * 1000, 2)
        return {"port": port, "open": False, "latency_ms": elapsed_ms, "error": str(e)}
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
            probes = [tcp_probe(ip, port) for port in PROBE_PORTS]
            any_open = any(p["open"] for p in probes)

            open_probes = [p for p in probes if p["open"]]
            latencies   = [p["latency_ms"] for p in open_probes] if open_probes else None
            avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else None

            send(200, {
                "tool":        L["tool"],
                "success":     True,
                "lang":        lang,
                "ip":          ip,
                "reachable":   any_open,
                "status":      L["reachable"] if any_open else L["unreachable"],
                "avg_latency_ms": avg_latency,
                "probes":      probes,
                "note":        L["note"],
            })
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error_net']}: {str(e)}"})

    def log_message(self, *args):
        pass
