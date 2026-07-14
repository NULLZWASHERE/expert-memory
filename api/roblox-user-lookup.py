from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

LABELS = {
    "en": {"title": "Roblox User Lookup", "error": "username or id parameter required"},
    "fr": {"title": "Recherche Utilisateur Roblox", "error": "Paramètre username ou id requis"}
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

        username = qs.get('username', [''])[0].strip()
        user_id = qs.get('id', [''])[0].strip()

        def fetch(url):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                return json.loads(r.read().decode())

        try:
            if username and not user_id:
                data = fetch('https://users.roblox.com/v1/usernames/users')
                # POST endpoint — do via urllib
                body = json.dumps({"usernames": [username], "excludeBannedUsers": False}).encode()
                req = urllib.request.Request(
                    'https://users.roblox.com/v1/usernames/users',
                    data=body,
                    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=8) as r:
                    result_data = json.loads(r.read().decode())
                users = result_data.get('data', [])
                if not users:
                    self.wfile.write(json.dumps({"error": "User not found"}).encode())
                    return
                user_id = str(users[0]['id'])

            if not user_id:
                self.wfile.write(json.dumps({"error": L["error"]}).encode())
                return

            user = fetch(f'https://users.roblox.com/v1/users/{user_id}')
            friends_count = fetch(f'https://friends.roblox.com/v1/users/{user_id}/friends/count')
            followers_count = fetch(f'https://friends.roblox.com/v1/users/{user_id}/followers/count')
            following_count = fetch(f'https://friends.roblox.com/v1/users/{user_id}/followings/count')
            try:
                avatar = fetch(f'https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false')
                avatar_url = avatar['data'][0]['imageUrl'] if avatar.get('data') else None
            except Exception:
                avatar_url = None

            result = {
                "tool": L["title"],
                "id": user.get("id"),
                "username": user.get("name"),
                "display_name": user.get("displayName"),
                "description": user.get("description"),
                "created_at": user.get("created"),
                "is_banned": user.get("isBanned"),
                "has_verified_badge": user.get("hasVerifiedBadge"),
                "external_app_display_name": user.get("externalAppDisplayName"),
                "profile_url": f"https://www.roblox.com/users/{user_id}/profile",
                "avatar_url": avatar_url,
                "social": {
                    "friends": friends_count.get("count"),
                    "followers": followers_count.get("count"),
                    "following": following_count.get("count"),
                },
            }
            self.wfile.write(json.dumps(result, indent=2).encode())

        except urllib.error.HTTPError as e:
            self.wfile.write(json.dumps({"error": f"Roblox API HTTP {e.code}"}).encode())
        except Exception as ex:
            self.wfile.write(json.dumps({"error": str(ex)}).encode())

    def log_message(self, *a): pass
