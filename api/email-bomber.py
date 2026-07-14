"""
VOID Tools — Email Bomber (Info / Authorized Testing Reference)
Returns SMTP configuration reference and authorized email stress-testing info.
The original tool sent SMTP emails — this API returns configuration info only.
Actual sending requires your own SMTP credentials and target authorization.
GET /api/email-bomber?lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

LABELS = {
    "en":{
        "tool":"Email Bomber",
        "note":"This API returns SMTP configuration reference only. Sending emails without authorization is illegal. Only use on systems/addresses you own or have explicit written permission to test.",
        "disclaimer":"Unauthorized email bombing is illegal in most jurisdictions (CFAA, CAN-SPAM, GDPR, etc.).",
    },
    "fr":{
        "tool":"Bombardier Email",
        "note":"Cette API retourne uniquement une référence de configuration SMTP. L'envoi d'emails sans autorisation est illégal. Utilisez uniquement sur des systèmes que vous possédez ou pour lesquels vous avez une autorisation écrite.",
        "disclaimer":"Le bombardement email non autorisé est illégal dans la plupart des juridictions.",
    },
}

SMTP_CONFIGS = [
    {"provider":"Gmail",   "host":"smtp.gmail.com","port_tls":587,"port_ssl":465,"requires_app_password":True,
     "note":"Requires App Password (2FA enabled). Limited to ~500/day."},
    {"provider":"Outlook", "host":"smtp-mail.outlook.com","port_tls":587,"port_ssl":465,"requires_app_password":False,
     "note":"Standard SMTP credentials."},
    {"provider":"Yahoo",   "host":"smtp.mail.yahoo.com","port_tls":587,"port_ssl":465,"requires_app_password":True,
     "note":"Requires App Password."},
    {"provider":"ProtonMail","host":"smtp.protonmail.ch","port_tls":587,"port_ssl":465,"requires_app_password":True,
     "note":"Requires Proton Bridge."},
    {"provider":"SendGrid","host":"smtp.sendgrid.net","port_tls":587,"port_ssl":465,"requires_app_password":True,
     "note":"Requires API key as password. High volume."},
    {"provider":"Mailgun", "host":"smtp.mailgun.org","port_tls":587,"port_ssl":465,"requires_app_password":True,
     "note":"Requires API key. High volume."},
]

PYTHON_SNIPPET = """import smtplib
from email.mime.text import MIMEText

def send_email(smtp_host, port, user, password, to, subject, body, count=1):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = user
    msg['To'] = to
    with smtplib.SMTP(smtp_host, port) as server:
        server.starttls()
        server.login(user, password)
        for _ in range(count):
            server.sendmail(user, to, msg.as_string())

# Example (use only on authorized targets):
# send_email('smtp.gmail.com', 587, 'you@gmail.com', 'app_password', 'target@example.com',
#            'Test', 'This is a stress test.', count=10)
"""

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

        send(200,{"tool":L["tool"],"success":True,"lang":lang,
                  "note":L["note"],"legal_disclaimer":L["disclaimer"],
                  "smtp_configurations":SMTP_CONFIGS,
                  "python_reference_snippet":PYTHON_SNIPPET,
                  "authorized_testing_services":[
                      {"name":"Mailosaur","url":"https://mailosaur.com/","desc":"Email testing platform"},
                      {"name":"Mailtrap","url":"https://mailtrap.io/","desc":"Email sandbox for testing"},
                      {"name":"Ethereal Email","url":"https://ethereal.email/","desc":"Fake SMTP for testing"},
                  ]})

    def log_message(self, *args): pass
