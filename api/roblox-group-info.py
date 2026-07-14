from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

LABELS = {
    "en": {"title": "Roblox Group Info", "error": "id parameter required (?id=...)"},
    "fr": {"title": "Info Groupe Roblox", "error": "Paramètre id requis (?id=...)"}
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get('lang', ['en'])[0]
        if lang not in LABELS: lang = 'en'
        L = LABELS[lang]

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        group_id = qs.get('id', [''])[0].strip()
        if not group_id:
            self.wfile.write(json.dumps({"error": L["error"]}).encode())
            return

        def fetch(url):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                return json.loads(r.read().decode())

        try:
            group = fetch(f'https://groups.roblox.com/v1/groups/{group_id}')
            try:
                roles = fetch(f'https://groups.roblox.com/v1/groups/{group_id}/roles')
                roles_list = roles.get('roles', [])
            except Exception:
                roles_list = []
            try:
                icon = fetch(f'https://thumbnails.roblox.com/v1/groups/icons?groupIds={group_id}&size=150x150&format=Png&isCircular=false')
                icon_url = icon['data'][0]['imageUrl'] if icon.get('data') else None
            except Exception:
                icon_url = None

            owner = group.get('owner') or {}
            shout = group.get('shout') or {}

            result = {
                "tool": L["title"],
                "id": group.get("id"),
                "name": group.get("name"),
                "description": group.get("description"),
                "member_count": group.get("memberCount"),
                "is_builders_club_only": group.get("isBuildersClubOnly"),
                "public_entry_allowed": group.get("publicEntryAllowed"),
                "has_verified_badge": group.get("hasVerifiedBadge"),
                "group_url": f"https://www.roblox.com/groups/{group_id}",
                "icon_url": icon_url,
                "owner": {
                    "user_id": owner.get("userId"),
                    "username": owner.get("username"),
                    "display_name": owner.get("displayName"),
                    "has_verified_badge": owner.get("hasVerifiedBadge"),
                } if owner else None,
                "shout": {
                    "body": shout.get("body"),
                    "poster": (shout.get("poster") or {}).get("username"),
                    "created": shout.get("created"),
                } if shout.get("body") else None,
                "roles": [{"id": r.get("id"), "name": r.get("name"), "rank": r.get("rank"), "member_count": r.get("memberCount")} for r in roles_list],
            }
            self.wfile.write(json.dumps(result, indent=2).encode())

        except urllib.error.HTTPError as e:
            self.wfile.write(json.dumps({"error": f"Roblox API HTTP {e.code}"}).encode())
        except Exception as ex:
            self.wfile.write(json.dumps({"error": str(ex)}).encode())

    def log_message(self, *a): pass
