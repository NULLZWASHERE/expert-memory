"""
VOID Tools — Number Info (Phone Number Analysis)
Vercel Python Serverless Function
GET /api/number-info?number=%2B33612345678&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier
    from phonenumbers import timezone as ph_timezone
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

NUMBER_TYPES = {
    0:  "Fixed Line",
    1:  "Mobile",
    2:  "Fixed or Mobile",
    3:  "Toll Free",
    4:  "Premium Rate",
    5:  "Shared Cost",
    6:  "VoIP",
    7:  "Personal",
    8:  "Pager",
    9:  "UAN",
    10: "Voicemail",
    -1: "Unknown",
} if not PHONENUMBERS_AVAILABLE else None

LABELS = {
    "en": {
        "tool": "Number Info",
        "missing": "Missing 'number' query parameter. Usage: /api/number-info?number=%2B33612345678",
        "invalid": "Invalid or unrecognized phone number.",
        "error": "Analysis error",
        "unavailable": "phonenumbers library not installed in this environment.",
        "valid": "Valid",
        "possible_yes": "Yes",
        "possible_no": "No",
    },
    "fr": {
        "tool": "Info Numéro",
        "missing": "Paramètre 'number' manquant. Utilisation : /api/number-info?number=%2B33612345678",
        "invalid": "Numéro de téléphone invalide ou non reconnu.",
        "error": "Erreur d'analyse",
        "unavailable": "La bibliothèque phonenumbers n'est pas installée.",
        "valid": "Valide",
        "possible_yes": "Oui",
        "possible_no": "Non",
    },
}

TYPE_MAP = {
    "en": {
        0: "Fixed Line", 1: "Mobile", 2: "Fixed or Mobile",
        3: "Toll Free", 4: "Premium Rate", 5: "Shared Cost",
        6: "VoIP", 7: "Personal", 8: "Pager", 9: "UAN", -1: "Unknown",
    },
    "fr": {
        0: "Ligne Fixe", 1: "Mobile", 2: "Fixe ou Mobile",
        3: "Numéro Gratuit", 4: "Surtaxé", 5: "Coût Partagé",
        6: "VoIP", 7: "Personnel", 8: "Pager", 9: "UAN", -1: "Inconnu",
    },
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        lang = params.get("lang", ["en"])[0].lower()
        if lang not in LABELS:
            lang = "en"
        L = LABELS[lang]

        number_list = params.get("number", [])

        def send(status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        if not number_list:
            send(400, {"tool": L["tool"], "success": False, "error": L["missing"]})
            return

        number = number_list[0].strip()

        if not PHONENUMBERS_AVAILABLE:
            send(503, {"tool": L["tool"], "success": False, "error": L["unavailable"]})
            return

        try:
            parsed_num = phonenumbers.parse(number, None)
        except phonenumbers.NumberParseException as e:
            send(400, {"tool": L["tool"], "success": False, "error": f"{L['invalid']} ({e})"})
            return

        if not phonenumbers.is_valid_number(parsed_num):
            send(400, {"tool": L["tool"], "success": False, "error": L["invalid"]})
            return

        try:
            num_type_id = phonenumbers.number_type(parsed_num)
            type_label  = TYPE_MAP.get(lang, TYPE_MAP["en"]).get(num_type_id, "Unknown")
            timezones   = ph_timezone.time_zones_for_number(parsed_num)
            tz          = timezones[0] if timezones else "Unknown"
            country     = phonenumbers.region_code_for_number(parsed_num) or "Unknown"
            region      = geocoder.description_for_number(parsed_num, lang if lang == "en" else "en") or "Unknown"
            operator    = carrier.name_for_number(parsed_num, "en") or "Unknown"
            possible    = phonenumbers.is_possible_number(parsed_num)

            send(200, {
                "tool":    L["tool"],
                "success": True,
                "lang":    lang,
                "data": {
                    "input":                number,
                    "national_format":      phonenumbers.format_number(parsed_num, phonenumbers.PhoneNumberFormat.NATIONAL),
                    "international_format": phonenumbers.format_number(parsed_num, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                    "e164_format":          phonenumbers.format_number(parsed_num, phonenumbers.PhoneNumberFormat.E164),
                    "status":               L["valid"],
                    "possible":             L["possible_yes"] if possible else L["possible_no"],
                    "country_code":         f"+{parsed_num.country_code}",
                    "country":              country,
                    "region":               region,
                    "timezone":             tz,
                    "operator":             operator,
                    "number_type":          type_label,
                }
            })
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error']}: {str(e)}"})

    def log_message(self, *args):
        pass
