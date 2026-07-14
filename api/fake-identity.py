from http.server import BaseHTTPRequestHandler
import json, secrets, random, time

FIRST_M = ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Charles","Christopher","Daniel","Matthew","Anthony","Mark","Donald","Steven","Paul","Andrew","Kenneth","Kevin","Brian","George","Timothy","Ronald","Edward","Jason","Jeffrey","Ryan","Jacob"]
FIRST_F = ["Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan","Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret","Sandra","Ashley","Emily","Dorothy","Kimberly","Carol","Michelle","Amanda","Melissa","Deborah","Stephanie","Rebecca","Sharon","Laura","Cynthia","Kathleen"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson"]
STREETS = ["Main St","Oak Ave","Maple Dr","Cedar Ln","Pine Rd","Elm St","Washington Blvd","Park Ave","Lake Dr","Hill Rd","River Rd","Forest Ave","Valley Dr","Summit Rd","Sunset Blvd"]
CITIES = [("New York","NY","10001"),("Los Angeles","CA","90001"),("Chicago","IL","60601"),("Houston","TX","77001"),("Phoenix","AZ","85001"),("Philadelphia","PA","19101"),("San Antonio","TX","78201"),("San Diego","CA","92101"),("Dallas","TX","75201"),("Austin","TX","73301")]
DOMAINS = ["gmail.com","yahoo.com","hotmail.com","outlook.com","icloud.com","protonmail.com","mail.com"]
USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"]
JOBS = ["Software Engineer","Teacher","Doctor","Nurse","Accountant","Marketing Manager","Sales Representative","Graphic Designer","Data Analyst","Project Manager","Electrician","Plumber","Chef","Lawyer","Architect"]
COMPANIES = ["Acme Corp","TechStart Inc","Global Solutions","NextGen Systems","Prime Industries","Alpha Technologies","Blue Ocean Ltd","Summit Enterprises","Horizon Group","Peak Performance Co"]

LABELS = {
    "en": {"title": "Fake Identity Generator"},
    "fr": {"title": "Générateur d'Identité Fictive"}
}

def luhn(n):
    digits = [int(d) for d in str(n)]
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd) + sum((d*2-9 if d*2>9 else d*2) for d in even)
    return total % 10 == 0

def fake_phone():
    area = random.randint(200,999)
    mid = random.randint(200,999)
    last = random.randint(1000,9999)
    return f"+1 ({area}) {mid}-{last}"

def fake_dob(min_age=18, max_age=70):
    import time
    now = time.localtime()
    year = now.tm_year - random.randint(min_age, max_age)
    month = random.randint(1,12)
    day = random.randint(1,28)
    return f"{year}-{month:02d}-{day:02d}"

def fake_ipv4():
    while True:
        o = [random.randint(1,254) for _ in range(4)]
        if o[0] not in (10,127,172,192): return '.'.join(map(str,o))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        if lang not in LABELS: lang = 'en'
        L = LABELS[lang]
        count = min(int(qs.get('count', ['1'])[0]), 10)
        gender = qs.get('gender', ['random'])[0].lower()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        identities = []
        for _ in range(count):
            g = gender if gender in ('male','female') else random.choice(('male','female'))
            first = random.choice(FIRST_M if g == 'male' else FIRST_F)
            last = random.choice(LAST)
            city, state, base_zip = random.choice(CITIES)
            zip_code = str(int(base_zip) + random.randint(0,99)).zfill(5)
            dob = fake_dob()
            username_base = (first[0] + last).lower()
            username = username_base + str(random.randint(1,9999))
            email = f"{username}@{random.choice(DOMAINS)}"
            password = secrets.token_urlsafe(16)
            identities.append({
                "name": {"first": first, "last": last, "full": f"{first} {last}"},
                "gender": g,
                "date_of_birth": dob,
                "phone": fake_phone(),
                "email": email,
                "username": username,
                "password": password,
                "address": {
                    "street": f"{random.randint(100,9999)} {random.choice(STREETS)}",
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "country": "United States"
                },
                "job": random.choice(JOBS),
                "company": random.choice(COMPANIES),
                "ip_address": fake_ipv4(),
                "user_agent": random.choice(USER_AGENTS),
            })

        self.wfile.write(json.dumps({
            "tool": L["title"],
            "count": count,
            "disclaimer": "Generated data is entirely fictional. For testing/educational purposes only.",
            "identities": identities
        }, indent=2).encode())

    def log_message(self, *a): pass
