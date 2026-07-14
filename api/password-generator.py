"""
VOID Tools — Password Generator
Vercel Python Serverless Function
GET /api/password-generator?length=16&count=5&symbols=true&numbers=true&upper=true&lower=true&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import secrets
import string

LABELS = {
    "en": {
        "tool": "Password Generator",
        "error_length": "Length must be between 4 and 128.",
        "error_count": "Count must be between 1 and 50.",
        "error_charset": "At least one character set must be enabled (symbols, numbers, upper, or lower).",
        "error": "Generation error",
    },
    "fr": {
        "tool": "Générateur de Mot de Passe",
        "error_length": "La longueur doit être comprise entre 4 et 128.",
        "error_count": "Le nombre doit être compris entre 1 et 50.",
        "error_charset": "Au moins un jeu de caractères doit être activé (symboles, chiffres, majuscules ou minuscules).",
        "error": "Erreur de génération",
    },
}

STRENGTH_LABELS = {
    "en": {1: "Weak", 2: "Fair", 3: "Good", 4: "Strong", 5: "Very Strong"},
    "fr": {1: "Faible", 2: "Passable", 3: "Bon", 4: "Fort", 5: "Très Fort"},
}


def assess_strength(password: str) -> int:
    score = 0
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1
    return max(1, min(score, 5))


def generate_password(length: int, charset: str) -> str:
    password = [secrets.choice(charset) for _ in range(length)]
    return ''.join(secrets.SystemRandom().sample(password, len(password)))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        lang = params.get("lang", ["en"])[0].lower()
        if lang not in LABELS:
            lang = "en"
        L = LABELS[lang]
        SL = STRENGTH_LABELS.get(lang, STRENGTH_LABELS["en"])

        def get_bool(key: str, default: bool = True) -> bool:
            val = params.get(key, [str(default).lower()])[0].lower()
            return val in ("true", "1", "yes", "oui")

        def send(status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        try:
            length = int(params.get("length", ["16"])[0])
        except ValueError:
            length = 16

        try:
            count = int(params.get("count", ["1"])[0])
        except ValueError:
            count = 1

        use_symbols = get_bool("symbols", True)
        use_numbers = get_bool("numbers", True)
        use_upper   = get_bool("upper", True)
        use_lower   = get_bool("lower", True)

        if not (4 <= length <= 128):
            send(400, {"tool": L["tool"], "success": False, "error": L["error_length"]})
            return

        if not (1 <= count <= 50):
            send(400, {"tool": L["tool"], "success": False, "error": L["error_count"]})
            return

        charset = ""
        if use_lower:   charset += string.ascii_lowercase
        if use_upper:   charset += string.ascii_uppercase
        if use_numbers: charset += string.digits
        if use_symbols: charset += string.punctuation

        if not charset:
            send(400, {"tool": L["tool"], "success": False, "error": L["error_charset"]})
            return

        try:
            passwords = []
            for _ in range(count):
                pw = generate_password(length, charset)
                strength_score = assess_strength(pw)
                passwords.append({
                    "password":        pw,
                    "length":          len(pw),
                    "strength_score":  strength_score,
                    "strength_label":  SL[strength_score],
                })

            send(200, {
                "tool":    L["tool"],
                "success": True,
                "lang":    lang,
                "config": {
                    "length":      length,
                    "count":       count,
                    "use_symbols": use_symbols,
                    "use_numbers": use_numbers,
                    "use_upper":   use_upper,
                    "use_lower":   use_lower,
                    "charset_size": len(charset),
                },
                "passwords": passwords,
            })
        except Exception as e:
            send(500, {"tool": L["tool"], "success": False, "error": f"{L['error']}: {str(e)}"})

    def log_message(self, *args):
        pass
