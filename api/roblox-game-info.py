from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

LABELS = {
    "en": {"title": "Roblox Game Info", "error": "id parameter required (?id=place_id or universe_id)"},
    "fr": {"title": "Info Jeu Roblox", "error": "Paramètre id requis (?id=...)"}
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

        place_id = qs.get('id', [''])[0].strip()
        if not place_id:
            self.wfile.write(json.dumps({"error": L["error"]}).encode())
            return

        def fetch(url):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                return json.loads(r.read().decode())

        try:
            # Get universe ID from place ID
            place_info = fetch(f'https://apis.roblox.com/universes/v1/places/{place_id}/universe')
            universe_id = place_info.get('universeId')
            if not universe_id:
                self.wfile.write(json.dumps({"error": "Could not resolve universe ID from place ID"}).encode())
                return

            game = fetch(f'https://games.roblox.com/v1/games?universeIds={universe_id}')
            games_list = game.get('data', [])
            if not games_list:
                self.wfile.write(json.dumps({"error": "Game not found"}).encode())
                return
            g = games_list[0]

            try:
                thumb = fetch(f'https://thumbnails.roblox.com/v1/games/icons?universeIds={universe_id}&returnPolicy=PlaceHolder&size=512x512&format=Png&isCircular=false')
                thumb_url = thumb['data'][0]['imageUrl'] if thumb.get('data') else None
            except Exception:
                thumb_url = None

            creator = g.get('creator', {})
            result = {
                "tool": L["title"],
                "universe_id": universe_id,
                "place_id": place_id,
                "name": g.get("name"),
                "description": g.get("description"),
                "creator": {
                    "id": creator.get("id"),
                    "name": creator.get("name"),
                    "type": creator.get("type"),
                    "has_verified_badge": creator.get("hasVerifiedBadge"),
                },
                "playing": g.get("playing"),
                "visits": g.get("visits"),
                "max_players": g.get("maxPlayers"),
                "created": g.get("created"),
                "updated": g.get("updated"),
                "is_for_18_plus": g.get("isForEighteenPlus"),
                "is_genre_enforced": g.get("isGenreEnforced"),
                "genre": g.get("genre"),
                "game_url": f"https://www.roblox.com/games/{place_id}",
                "thumbnail_url": thumb_url,
                "votes": {
                    "up_votes": g.get("upVotes"),
                    "down_votes": g.get("downVotes"),
                    "rating_pct": round(g.get("upVotes", 0) / max(g.get("upVotes", 0) + g.get("downVotes", 1), 1) * 100, 1) if g.get("upVotes") else None,
                },
            }
            self.wfile.write(json.dumps(result, indent=2).encode())
        except urllib.error.HTTPError as e:
            self.wfile.write(json.dumps({"error": f"Roblox API HTTP {e.code}"}).encode())
        except Exception as ex:
            self.wfile.write(json.dumps({"error": str(ex)}).encode())

    def log_message(self, *a): pass
