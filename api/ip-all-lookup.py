"""
VOID Tools — IP All Lookup
Combines: ipinfo.io (full info) + ip-api.com (geo+ISP) + port scan + reverse DNS
GET /api/ip-all-lookup?ip=1.2.3.4&lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, re, socket, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

IPINFO_TOKEN = "691b5da3c2ffa2"
TIMEOUT = 8
IP_REGEX = re.compile(r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
COMMON_PORTS = {21:"FTP",22:"SSH",80:"HTTP",443:"HTTPS",3306:"MySQL",3389:"RDP",8080:"HTTP-alt"}

LABELS = {
    "en": {"tool":"IP All Lookup","missing":"Missing 'ip'. Usage: /api/ip-all-lookup?ip=8.8.8.8","invalid":"Invalid IP format.","error":"Error"},
    "fr": {"tool":"Lookup IP Complet","missing":"Paramètre 'ip' manquant.","invalid":"Format IP invalide.","error":"Erreur"},
}

def fetch_ipinfo(ip):
    req = urllib.request.Request(f"https://ipinfo.io/{ip}?token={IPINFO_TOKEN}", headers={"User-Agent":"VoidTools/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r: return json.loads(r.read())

def fetch_ipapi(ip):
    req = urllib.request.Request(f"https://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,isp,org,as,asname,query,proxy,hosting,mobile", headers={"User-Agent":"VoidTools/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r: return json.loads(r.read())

def scan_port(ip, port, timeout=1.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(timeout)
    try: return port, s.connect_ex((ip, port)) == 0
    except: return port, False
    finally: s.close()

def reverse_dns(ip):
    try: return socket.gethostbyaddr(ip)[0]
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
            with ThreadPoolExecutor(max_workers=4) as ex:
                f_ipinfo  = ex.submit(fetch_ipinfo, ip)
                f_ipapi   = ex.submit(fetch_ipapi, ip)
                f_rdns    = ex.submit(reverse_dns, ip)
                port_futs = {ex.submit(scan_port, ip, p): p for p in COMMON_PORTS}

            ipinfo = f_ipinfo.result() if not f_ipinfo.exception() else {}
            ipapi  = f_ipapi.result()  if not f_ipapi.exception()  else {}
            rdns   = f_rdns.result()

            ports = []
            for fut, port in port_futs.items():
                _, is_open = fut.result()
                ports.append({"port":port,"service":COMMON_PORTS[port],"open":is_open})
            ports.sort(key=lambda x: x["port"])

            send(200,{
                "tool":L["tool"],"success":True,"lang":lang,"ip":ip,
                "ipinfo": {
                    "city":ipinfo.get("city","N/A"),"region":ipinfo.get("region","N/A"),
                    "country":ipinfo.get("country","N/A"),"postal":ipinfo.get("postal","N/A"),
                    "coordinates":ipinfo.get("loc","N/A"),"organization":ipinfo.get("org","N/A"),
                    "timezone":ipinfo.get("timezone","N/A"),"hostname":ipinfo.get("hostname","N/A"),
                },
                "geolocation": {
                    "country":ipapi.get("country","N/A"),"region":ipapi.get("regionName","N/A"),
                    "city":ipapi.get("city","N/A"),"zip":ipapi.get("zip","N/A"),
                    "latitude":ipapi.get("lat","N/A"),"longitude":ipapi.get("lon","N/A"),
                },
                "network": {
                    "isp":ipapi.get("isp","N/A"),"org":ipapi.get("org","N/A"),
                    "as":ipapi.get("as","N/A"),"as_name":ipapi.get("asname","N/A"),
                    "is_proxy":ipapi.get("proxy",False),"is_hosting":ipapi.get("hosting",False),
                    "is_mobile":ipapi.get("mobile",False),
                },
                "reverse_dns": rdns or "N/A",
                "ports": ports,
                "open_ports": [p for p in ports if p["open"]],
            })
        except Exception as e:
            send(500,{"tool":L["tool"],"success":False,"error":f"{L['error']}: {e}"})

    def log_message(self, *args): pass
