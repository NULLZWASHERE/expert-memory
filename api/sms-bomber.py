"""
VOID Tools — SMS Bomber (Info / Reference Only)
Returns SMS testing service references and authorized stress-test info only.
GET /api/sms-bomber?lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

LABELS = {
    "en":{"tool":"SMS Bomber","note":"This endpoint returns authorized SMS testing services only. Sending unsolicited SMS is illegal. Use only on phone numbers you own or have explicit permission to test.",
          "disclaimer":"Unauthorized SMS bombing violates the TCPA, GDPR, and telecommunications laws in most countries."},
    "fr":{"tool":"Bombardier SMS","note":"Ce endpoint retourne uniquement des services de test SMS autorisés. L'envoi de SMS non sollicités est illégal.",
          "disclaimer":"Le bombardement SMS non autorisé viole les lois sur les télécommunications dans la plupart des pays."},
}

TESTING_SERVICES = [
    {"name":"Twilio","url":"https://www.twilio.com/","type":"SMS API","note":"Industry standard. Free trial available."},
    {"name":"Vonage (Nexmo)","url":"https://www.vonage.com/","type":"SMS API","note":"REST API for SMS."},
    {"name":"AWS SNS","url":"https://aws.amazon.com/sns/","type":"SMS API","note":"Amazon Simple Notification Service."},
    {"name":"TextMagic","url":"https://www.textmagic.com/","type":"SMS API","note":"Bulk SMS with API."},
    {"name":"ClickSend","url":"https://www.clicksend.com/","type":"SMS API","note":"REST API + free credits."},
    {"name":"BulkSMS","url":"https://www.bulksms.com/","type":"SMS API","note":"Bulk SMS gateway."},
]

PYTHON_SNIPPET = """# Using Twilio (authorized testing only)
# pip install twilio
from twilio.rest import Client

account_sid = 'YOUR_ACCOUNT_SID'
auth_token = 'YOUR_AUTH_TOKEN'
client = Client(account_sid, auth_token)

def send_sms(to, from_, body, count=1):
    for _ in range(count):
        msg = client.messages.create(body=body, from_=from_, to=to)
        print(f'Sent: {msg.sid}')

# Example (use only on numbers you own):
# send_sms('+1234567890', '+19876543210', 'Test message', count=5)
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
                  "testing_services":TESTING_SERVICES,
                  "python_reference_snippet":PYTHON_SNIPPET})

    def log_message(self, *args): pass
