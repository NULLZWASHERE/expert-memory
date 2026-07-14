"""
VOID Tools — Temp Mail
Returns a curated list of temporary / disposable email services.
Also generates a random address string for use on those services.
GET /api/temp-mail?lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, secrets, string

LABELS = {
    "en":{"tool":"Temp Mail","desc":"Disposable / temporary email services"},
    "fr":{"tool":"Mail Temporaire","desc":"Services de messagerie jetable / temporaire"},
}

SERVICES = [
    {"name":"10MinuteMail",  "url":"https://10minutemail.com/",       "api":False,"note":"Auto-generated address, 10 min expiry"},
    {"name":"Guerrilla Mail","url":"https://guerrillamail.com/",       "api":True, "note":"Public API available"},
    {"name":"TempMail",      "url":"https://temp-mail.org/",          "api":True, "note":"REST API available"},
    {"name":"Mailnull",      "url":"https://www.mailnull.com/",       "api":False,"note":"Simple redirect service"},
    {"name":"Dispostable",   "url":"https://dispostable.com/",        "api":False,"note":"Simple disposable inbox"},
    {"name":"FakeMail",      "url":"https://www.fakemail.net/",       "api":False,"note":"Random address generator"},
    {"name":"MailDrop",      "url":"https://maildrop.cc/",            "api":True, "note":"Public API, custom inboxes"},
    {"name":"Yopmail",       "url":"https://www.yopmail.com/",        "api":False,"note":"Persistent inbox by name"},
    {"name":"Mailinator",    "url":"https://www.mailinator.com/",     "api":True, "note":"Public inboxes + API"},
    {"name":"Inboxbear",     "url":"https://inboxbear.com/",          "api":False,"note":"Simple throwaway inbox"},
    {"name":"ThrowAM",       "url":"https://www.throwam.com/",        "api":False,"note":"Instant temp mail"},
    {"name":"SpamGourmet",   "url":"https://www.spamgourmet.com/",    "api":False,"note":"Forwarding + filtering"},
    {"name":"TrashMail",     "url":"https://trashmail.com/",          "api":True, "note":"API available, redirect mail"},
    {"name":"GuerrillaAPI",  "url":"https://www.guerrillamail.com/GuerrillaMailAPI.html","api":True,"note":"REST API docs"},
]

COMMON_DOMAINS = ["mailnull.com","guerrillamail.com","maildrop.cc","yopmail.com","mailinator.com","dispostable.com"]

def random_address():
    chars = string.ascii_lowercase + string.digits
    user = ''.join(secrets.choice(chars) for _ in range(12))
    domain = secrets.choice(COMMON_DOMAINS)
    return f"{user}@{domain}"

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

        suggestions = [random_address() for _ in range(5)]
        send(200,{"tool":L["tool"],"success":True,"lang":lang,"description":L["desc"],
                  "suggested_addresses":suggestions,
                  "note":"These addresses may or may not be inboxes. Visit the service URL to receive mail.",
                  "services":SERVICES,"total":len(SERVICES)})

    def log_message(self, *args): pass
