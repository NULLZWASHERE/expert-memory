"""
VOID Tools — VPN / Proxy / Tor Detector
Uses ip-api.com proxy detection + ip.teoh.io + multiple check layers.
GET /api/vpn-detector?ip=1.2.3.4&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, re, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 6
IP_REGEX = re.compile(r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')

LABELS = {
    "en":{"tool":"VPN / Proxy Detector","missing":"Missing 'ip'. Usage: /api/vpn-detector?ip=1.2.3.4","invalid":"Invalid IP format.","error":"Error"},
    "fr":{"tool":"Détecteur VPN / Proxy","missing":"Paramètre 'ip' manquant.","invalid":"Format IP invalide.","error":"Erreur"},
}

INTEL_LINKS = [
    ("IPQualityScore","https://ipqualityscore.com/free-ip-lookup-proxy-vpn-test/lookup/{}"),
    ("IPHub",        "https://iphub.info/ip/{}"),
    ("ProxyCheck.io","https://proxycheck.io/v2/{}?vpn=1&asn=1"),
    ("GetIPIntel",   "https://check.getipintel.net/check.php?ip={}&contact=void@tools.io"),
    ("ScamaLytics",  "https://scamalytics.com/ip/{}"),
]

def check_ipapi(ip):
    url = f"https://ip-api.com/json/{ip}?fields=status,message,proxy,hosting,mobile,isp,org,as,asname,country,city,query"
    req = urllib.request.Request(url, headers={"User-Agent":"VoidTools/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        if d.get("status")=="fail": return None
        return {"source":"ip-api.com","is_proxy":d.get("proxy",False),"is_hosting":d.get("hosting",False),
                "is_mobile":d.get("mobile",False),"isp":d.get("isp","N/A"),"org":d.get("org","N/A"),
                "as":d.get("as","N/A"),"country":d.get("country","N/A"),"city":d.get("city","N/A")}
    except: return None

def check_teoh(ip):
    url = f"https://ip.teoh.io/api/vpn/{ip}"
    req = urllib.request.Request(url, headers={"User-Agent":"VoidTools/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        return {"source":"ip.teoh.io","is_vpn":d.get("is_vpn",False),"is_tor":d.get("is_tor",False),
                "is_hosting":d.get("is_hosting",False),"vpn_or_tor":d.get("vpn_or_tor",False)}
    except: return None

def check_cloudflare(ip):
    url = f"https://api.cloudflare.com/client/v4/ips"
    req = urllib.request.Request(f"https://ipinfo.io/{ip}/json", headers={"User-Agent":"VoidTools/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read())
        org = d.get("org","").lower()
        is_vpn_like = any(kw in org for kw in ["vpn","proxy","hosting","cloud","datacenter","digitalocean","linode","aws","azure","google"])
        return {"source":"ipinfo.io","org":d.get("org","N/A"),"hostname":d.get("hostname","N/A"),
                "likely_vpn_or_datacenter":is_vpn_like}
    except: return None

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

        ip_list = params.get("ip",[])
        if not ip_list: send(400,{"tool":L["tool"],"success":False,"error":L["missing"]}); return
        ip = ip_list[0].strip()
        if not IP_REGEX.match(ip): send(400,{"tool":L["tool"],"success":False,"error":L["invalid"],"input":ip}); return

        try:
            with ThreadPoolExecutor(max_workers=3) as ex:
                f1 = ex.submit(check_ipapi, ip)
                f2 = ex.submit(check_teoh, ip)
                f3 = ex.submit(check_cloudflare, ip)
            r1,r2,r3 = f1.result(),f2.result(),f3.result()

            verdict_flags = []
            if r1 and (r1.get("is_proxy") or r1.get("is_hosting")): verdict_flags.append("proxy/hosting (ip-api)")
            if r2 and (r2.get("is_vpn") or r2.get("is_tor")): verdict_flags.append("vpn/tor (teoh.io)")
            if r3 and r3.get("likely_vpn_or_datacenter"): verdict_flags.append("datacenter/vpn-org (ipinfo)")

            send(200,{
                "tool":L["tool"],"success":True,"lang":lang,"ip":ip,
                "verdict":{"likely_vpn_proxy_tor": len(verdict_flags)>0,"flags":verdict_flags},
                "checks":[r for r in [r1,r2,r3] if r],
                "intel_links":[{"name":n,"url":u.format(ip)} for n,u in INTEL_LINKS],
            })
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
