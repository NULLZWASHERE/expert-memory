"""
VOID Tools — Domain Intel
DNS records (A/AAAA/MX/NS/TXT/CNAME), WHOIS links, SSL cert info, HTTP headers.
GET /api/domain-intel?domain=google.com&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json, re, ssl, socket, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

TIMEOUT = 6
DOMAIN_RE = re.compile(r'^(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$', re.I)

LABELS = {
    "en":{"tool":"Domain Intel","missing":"Missing 'domain'. Usage: /api/domain-intel?domain=google.com","invalid":"Invalid domain name.","error":"Error"},
    "fr":{"tool":"Intelligence Domaine","missing":"Paramètre 'domain' manquant.","invalid":"Nom de domaine invalide.","error":"Erreur"},
}

def dns_query(name, rtype):
    try:
        url = f"https://dns.google/resolve?name={quote(name)}&type={rtype}"
        req = urllib.request.Request(url, headers={"Accept":"application/dns-json","User-Agent":"VoidTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read())
        return [a.get("data","") for a in data.get("Answer",[])]
    except: return []

def get_http_headers(domain):
    try:
        req = urllib.request.Request(f"https://{domain}", headers={"User-Agent":"VoidTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            hdrs = dict(r.headers)
            return {"status_code":r.status,"url":r.url,
                    "server":hdrs.get("server","N/A"),"x_powered_by":hdrs.get("x-powered-by","N/A"),
                    "content_type":hdrs.get("content-type","N/A"),"strict_transport_security":hdrs.get("strict-transport-security","N/A"),
                    "x_frame_options":hdrs.get("x-frame-options","N/A"),"content_security_policy":hdrs.get("content-security-policy","present" if "content-security-policy" in hdrs else "absent")}
    except urllib.error.HTTPError as e:
        return {"status_code":e.code,"error":str(e)}
    except Exception as e:
        return {"status_code":None,"error":str(e)}

def get_ssl_info(domain):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.create_connection((domain,443),timeout=TIMEOUT),server_hostname=domain) as sock:
            cert = sock.getpeercert()
        subject = dict(x[0] for x in cert.get("subject",[]))
        issuer  = dict(x[0] for x in cert.get("issuer",[]))
        san = [v for _,v in cert.get("subjectAltName",[])]
        return {"valid":True,"common_name":subject.get("commonName","N/A"),
                "issuer":issuer.get("organizationName","N/A"),"issuer_cn":issuer.get("commonName","N/A"),
                "not_before":cert.get("notBefore","N/A"),"not_after":cert.get("notAfter","N/A"),
                "san":san[:10]}
    except ssl.SSLCertVerificationError: return {"valid":False,"error":"Certificate verification failed"}
    except Exception as e: return {"valid":None,"error":str(e)}

def get_ip(domain):
    try: return socket.gethostbyname(domain)
    except: return None

INTEL_LINKS = [
    ("WHOIS",      "https://who.is/whois/{}"),
    ("DNS Checker","https://dnschecker.org/#A/{}"),
    ("Subdomains", "https://subdomainfinder.c99.nl/?domain={}"),
    ("SSL Cert",   "https://crt.sh/?q={}"),
    ("VirusTotal", "https://virustotal.com/gui/domain/{}"),
    ("Shodan",     "https://shodan.io/search?query=hostname%3A{}"),
    ("URLScan",    "https://urlscan.io/search/#domain%3A{}"),
    ("SecurityTrails","https://securitytrails.com/domain/{}/dns"),
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

        dom_list = params.get("domain",[])
        if not dom_list or not dom_list[0].strip(): send(400,{"tool":L["tool"],"success":False,"error":L["missing"]}); return
        domain = dom_list[0].strip().lower().lstrip("https://").lstrip("http://").rstrip("/")
        if not DOMAIN_RE.match(domain): send(400,{"tool":L["tool"],"success":False,"error":L["invalid"],"input":domain}); return

        try:
            with ThreadPoolExecutor(max_workers=8) as ex:
                fa   = ex.submit(dns_query, domain, "A")
                faaaa= ex.submit(dns_query, domain, "AAAA")
                fmx  = ex.submit(dns_query, domain, "MX")
                fns  = ex.submit(dns_query, domain, "NS")
                ftxt = ex.submit(dns_query, domain, "TXT")
                fcname=ex.submit(dns_query, domain, "CNAME")
                fhttp= ex.submit(get_http_headers, domain)
                fssl = ex.submit(get_ssl_info, domain)

            ip = fa.result()[0] if fa.result() else get_ip(domain)
            send(200,{
                "tool":L["tool"],"success":True,"lang":lang,"domain":domain,
                "resolved_ip": ip,
                "dns":{"a":fa.result(),"aaaa":faaaa.result(),"mx":fmx.result(),
                       "ns":fns.result(),"txt":ftxt.result()[:5],"cname":fcname.result()},
                "http": fhttp.result(),
                "ssl":  fssl.result(),
                "intel_links":[{"name":n,"url":u.format(domain)} for n,u in INTEL_LINKS],
            })
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
