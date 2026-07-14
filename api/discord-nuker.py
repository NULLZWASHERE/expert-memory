"""
VOID Tools — Discord Nuker Info
Returns information about Discord server management/nuker capabilities.
Actual nuking requires the Void-Nuke bot: https://github.com/void4real/Void-Nuke
GET /api/discord-nuker?lang=en
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

LABELS = {
    "en":{"tool":"Discord Nuker","note":"This API returns feature information only. Only use on servers you own. Raiding/nuking servers without permission is against Discord ToS and may be illegal.",
          "disclaimer":"Unauthorized server raiding violates Discord Terms of Service and may be illegal."},
    "fr":{"tool":"Nuker Discord","note":"Cette API retourne uniquement des informations sur les fonctionnalités. Utilisez uniquement sur vos propres serveurs.",
          "disclaimer":"Le raid non autorisé viole les CGU de Discord et peut être illégal."},
}

FEATURES_PAGE1 = [
    {"id":"01","name":"Nuke",              "desc":"Combined mass-action: ban all + delete channels + spam"},
    {"id":"02","name":"Auto Raid",         "desc":"Automated raid sequence"},
    {"id":"03","name":"Ban All",           "desc":"Mass ban all server members"},
    {"id":"04","name":"Kick All",          "desc":"Mass kick all server members"},
    {"id":"05","name":"Mute All",          "desc":"Mute all members in voice channels"},
    {"id":"06","name":"Unban All",         "desc":"Remove all bans from a server"},
    {"id":"07","name":"Delete Channels",   "desc":"Delete all text/voice channels"},
    {"id":"08","name":"Delete Emojis",     "desc":"Remove all custom emojis"},
    {"id":"09","name":"Delete Stickers",   "desc":"Remove all custom stickers"},
    {"id":"10","name":"Create Channels",   "desc":"Mass create text channels"},
    {"id":"11","name":"Create Roles",      "desc":"Mass create roles"},
    {"id":"12","name":"Create Categories", "desc":"Mass create category channels"},
]

FEATURES_PAGE2 = [
    {"id":"01","name":"Rename Channels",   "desc":"Bulk rename all channels"},
    {"id":"02","name":"Rename Roles",      "desc":"Bulk rename all roles"},
    {"id":"03","name":"Edit Server",       "desc":"Change server name/icon"},
    {"id":"04","name":"Ghost Ping",        "desc":"Ping and immediately delete"},
    {"id":"05","name":"DM Spam",           "desc":"Send DMs to all members"},
    {"id":"06","name":"Webhook Spam",      "desc":"Spam via server webhooks"},
    {"id":"07","name":"Lockdown",          "desc":"Lock all channels"},
    {"id":"08","name":"Clone Server",      "desc":"Clone server structure"},
    {"id":"09","name":"Message All",       "desc":"Send message in all channels"},
    {"id":"10","name":"Mass Spam",         "desc":"Mass message spam"},
    {"id":"11","name":"Mass Ban",          "desc":"Ban users by ID list"},
    {"id":"12","name":"Mass Kick",         "desc":"Kick users by ID list"},
]

DISCORD_TOOLS = [
    {"id":"T1","name":"Token Checker",  "desc":"Validate a Discord user token","endpoint":"/api/discord-token-checker"},
    {"id":"T2","name":"Server Cloner",  "desc":"Clone server structure","external":"https://github.com/void4real/Void-Nuke"},
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

        send(200,{"tool":L["tool"],"success":True,"lang":lang,
                  "note":L["note"],"legal_disclaimer":L["disclaimer"],
                  "source":"https://github.com/void4real/Void-Nuke",
                  "features_page1":FEATURES_PAGE1,
                  "features_page2":FEATURES_PAGE2,
                  "discord_tools":DISCORD_TOOLS,
                  "total_features":len(FEATURES_PAGE1)+len(FEATURES_PAGE2)})

    def log_message(self, *args): pass
