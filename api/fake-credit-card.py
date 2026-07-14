from http.server import BaseHTTPRequestHandler
import json, random, secrets

LABELS = {
    "en": {"title": "Fake Credit Card Generator"},
    "fr": {"title": "Générateur de Carte de Crédit Fictive"}
}

BRANDS = {
    "visa":       {"prefix": ["4"], "length": 16, "cvv": 3},
    "mastercard": {"prefix": ["51","52","53","54","55"], "length": 16, "cvv": 3},
    "amex":       {"prefix": ["34","37"], "length": 15, "cvv": 4},
    "discover":   {"prefix": ["6011","65"], "length": 16, "cvv": 3},
    "jcb":        {"prefix": ["35"], "length": 16, "cvv": 3},
}

def luhn_complete(partial):
    digits = list(map(int, partial))
    check = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            d *= 2
            if d > 9: d -= 9
        check += d
    return (10 - check % 10) % 10

def generate_card(brand):
    info = BRANDS[brand]
    prefix = random.choice(info["prefix"])
    length = info["length"]
    partial = prefix + ''.join([str(random.randint(0,9)) for _ in range(length - len(prefix) - 1)])
    check_digit = luhn_complete(partial)
    number = partial + str(check_digit)
    month = random.randint(1, 12)
    year = random.randint(2026, 2032)
    cvv = ''.join([str(random.randint(0,9)) for _ in range(info["cvv"])])
    formatted = ' '.join([number[i:i+4] for i in range(0, len(number), 4)])
    return {
        "brand": brand.upper(),
        "number": number,
        "formatted": formatted.strip(),
        "expiry": f"{month:02d}/{year}",
        "cvv": cvv,
        "length": length,
        "luhn_valid": True,
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        if lang not in LABELS: lang = 'en'
        L = LABELS[lang]
        brand = qs.get('brand', ['random'])[0].lower()
        count = min(int(qs.get('count', ['5'])[0]), 20)

        if brand == 'random' or brand not in BRANDS:
            brands = [random.choice(list(BRANDS.keys())) for _ in range(count)]
        else:
            brands = [brand] * count

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        cards = [generate_card(b) for b in brands]
        self.wfile.write(json.dumps({
            "tool": L["title"],
            "count": count,
            "disclaimer": "These are NOT real credit cards. Generated for testing/development only. Numbers pass Luhn check but are not associated with any real account.",
            "available_brands": list(BRANDS.keys()),
            "cards": cards,
        }, indent=2).encode())

    def log_message(self, *a): pass
