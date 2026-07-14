"""
VOID Tools — Simple Dox
Quick dox report: username, name, age, address, phone, IP.
GET /api/simple-dox?username=johndoe&name=John+Doe&age=25&address=...&phone=...&ip=...&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime, timezone

LABELS = {
    "en":{"tool":"Simple Dox","note":"For authorized research only. Misuse is illegal."},
    "fr":{"tool":"Dox Simple","note":"Pour la recherche autorisée uniquement. Toute utilisation abusive est illégale."},
}

FIELDS = [
    ("username","Username"),("name","Full Name"),("age","Age"),
    ("address","Address"),("phone","Phone Number"),("ip","IP Address"),
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); params = parse_qs(parsed.query)
        lang = params.get("lang",["en"])[0].lower()
        if lang not in LABELS: lang = "en"
        L = LABELS[lang]

        def send(status, payload):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)

        data = {}
        for key, label in FIELDS:
            val = params.get(key,[""])[0].strip()
            data[key] = {"label":label,"value":val if val else "N/A"}

        dox_name = params.get("dox_name",["unnamed"])[0].strip() or "unnamed"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "╔══════════════════════════════╗",
            "║  VOID TOOLS — SIMPLE DOX     ║",
            f"║  {ts[:27]:<28}║",
            "╚══════════════════════════════╝",
            "",
            "── Collected Information ──────",
        ]
        for k, label in FIELDS:
            lines.append(f"  {label:<16}: {data[k]['value']}")
        lines += ["","── VOID TOOLS ─────────────────"]

        send(200,{
            "tool":L["tool"],"success":True,"lang":lang,
            "dox_name":dox_name,"generated_at":ts,
            "note":L["note"],"data":data,
            "report":"\n".join(lines),
        })

    def log_message(self, *args): pass
