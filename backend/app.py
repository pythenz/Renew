# backend/app.py
import os
import json
import time
from functools import wraps
from urllib.parse import urlencode

from flask import Flask, request, session, redirect, jsonify, send_file
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Optional translator lib (Libre via deep_translator)
try:
    from deep_translator import LibreTranslator
    TRANSLATOR_AVAILABLE = True
except Exception:
    TRANSLATOR_AVAILABLE = False

load_dotenv()

# ---------- Config (env) ----------
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")
OAUTH_REDIRECT = os.getenv("OAUTH_REDIRECT", "https://your-frontend.example.com/api/auth/callback")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
SUPABASE_URL = os.getenv("SUPABASE_URL")      # e.g. https://xyz.supabase.co
SUPABASE_KEY = os.getenv("SUPABASE_KEY")      # anon or service_role (service_role needed for inserts)
TRANSLATE_PROVIDER = os.getenv("TRANSLATE_PROVIDER", "libre")  # libre | google | deepl
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")

# ---------- Flask init ----------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", os.urandom(24))
CORS(app, origins=[FRONTEND_ORIGIN])

# ---------- Helpers ----------
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # session token or Authorization header (Bearer <token>)
        token = session.get("access_token") or request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper

def discord_oauth_url(state=None, scopes=None):
    if scopes is None:
        scopes = ["identify", "guilds"]
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": OAUTH_REDIRECT,
        "response_type": "code",
        "scope": " ".join(scopes),
    }
    if state:
        params["state"] = state
    return f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"

def exchange_code_for_token(code):
    url = "https://discord.com/api/oauth2/token"
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": OAUTH_REDIRECT,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(url, data=data, headers=headers)
    return resp.json()

def get_user_guilds(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get("https://discord.com/api/v10/users/@me/guilds", headers=headers)
    return resp.json()

def bot_api_get(path):
    """Helper to GET Discord API with bot token. path is after /api"""
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    url = f"https://discord.com/api/v10{path}"
    r = requests.get(url, headers=headers)
    if r.status_code >= 400:
        raise Exception(f"Discord GET {url} failed: {r.status_code} {r.text}")
    return r.json()

def bot_api_post(path, json_body):
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}
    url = f"https://discord.com/api/v10{path}"
    r = requests.post(url, headers=headers, json=json_body)
    if r.status_code >= 400:
        raise Exception(f"Discord POST {url} failed: {r.status_code} {r.text}")
    return r.json()

def save_backup_to_supabase(guild_id, snapshot):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False, "Supabase not configured"
    # Assumes a table named server_backups with columns (guild_id text, snapshot json)
    url = f"{SUPABASE_URL}/rest/v1/server_backups"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    payload = {"guild_id": guild_id, "snapshot": snapshot}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code in (200,201):
        return True, r.json()
    return False, r.text

def get_backup_from_supabase(guild_id):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/server_backups?guild_id=eq.{guild_id}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None
    arr = r.json()
    return arr[-1] if arr else None

# Local fallback storage folder
BACKUP_FOLDER = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_FOLDER, exist_ok=True)

def save_backup_local(guild_id, snapshot):
    path = os.path.join(BACKUP_FOLDER, f"{guild_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    return path

def load_backup_local(guild_id):
    path = os.path.join(BACKUP_FOLDER, f"{guild_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- Routes: OAuth ----------
@app.route("/api/auth/url")
def auth_url():
    return jsonify({"url": discord_oauth_url()})

@app.route("/api/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return "missing code", 400
    token_data = exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        return jsonify(token_data), 400
    session["access_token"] = access_token
    return redirect(FRONTEND_ORIGIN)

# ---------- Simple protected route: list guilds ----------
@app.route("/api/me/guilds")
@require_auth
def api_guilds():
    token = session.get("access_token") or request.headers.get("Authorization")
    guilds = get_user_guilds(token)
    return jsonify(guilds)

# ---------- Backup: FULL server snapshot ----------
@app.route("/api/guilds/<guild_id>/backup", methods=["GET","POST"])
@require_auth
def backup_guild(guild_id):
    """
    GET -> returns existing backup (from Supabase or local)
    POST -> create & store a fresh backup snapshot by calling Discord API (bot token required)
    """
    if request.method == "GET":
        # try supabase first
        sb = get_backup_from_supabase(guild_id)
        if sb:
            return jsonify(sb)
        local = load_backup_local(guild_id)
        if local:
            return jsonify({"guild_id": guild_id, "snapshot": local})
        return jsonify({"error": "no backup found"}), 404

    # POST: create snapshot
    try:
        # fetch guild metadata
        guild_info = bot_api_get(f"/guilds/{guild_id}")
        roles = bot_api_get(f"/guilds/{guild_id}/roles")
        channels = bot_api_get(f"/guilds/{guild_id}/channels")
        emojis = bot_api_get(f"/guilds/{guild_id}/emojis")
        # we capture basic structures and permission_overwrites
        snapshot = {
            "guild_info": guild_info,
            "roles": roles,
            "channels": channels,
            "emojis": emojis,
            "created_at": int(time.time())
        }
    except Exception as e:
        return jsonify({"error": "failed to fetch guild data", "details": str(e)}), 500

    # try saving to Supabase table server_backups
    ok, res = save_backup_to_supabase(guild_id, snapshot)
    if ok:
        return jsonify({"ok": True, "saved_to": "supabase", "data": res}), 201

    # fallback: save local file
    path = save_backup_local(guild_id, snapshot)
    return jsonify({"ok": True, "saved_to": "local", "path": path}), 201

# ---------- Restore from backup (DANGEROUS) ----------
@app.route("/api/guilds/<guild_id>/restore", methods=["POST"])
@require_auth
def restore_guild(guild_id):
    """
    Restores a guild from the latest snapshot stored.
    Expect JSON body: {"confirm": true}
    WARNING: This performs destructive actions (creates roles/channels). Confirm explicitly.
    """
    body = request.json or {}
    if not body.get("confirm"):
        return jsonify({"error": "operation not confirmed. send {\"confirm\": true} to proceed."}), 400

    # load snapshot (supabase first then local)
    sb = get_backup_from_supabase(guild_id)
    snapshot = None
    if sb and isinstance(sb, (list, dict)):
        # supabase row might be list; normalize
        if isinstance(sb, list) and len(sb) > 0:
            snapshot = sb[-1].get("snapshot")
        elif isinstance(sb, dict):
            snapshot = sb.get("snapshot")
    if not snapshot:
        snapshot = load_backup_local(guild_id)
    if not snapshot:
        return jsonify({"error": "no backup found for this guild"}), 404

    # NOTE: The restore process requires the bot to have MANAGE_ROLES, MANAGE_CHANNELS permissions in the target guild.
    # We'll attempt to recreate roles (skipping @everyone) then channels with basic perms.
    created = {"roles": [], "channels": []}
    try:
        # restore roles
        for r in snapshot.get("roles", []):
            # skip @everyone (id == guild_id usually)
            if r.get("name", "").lower() == "@everyone":
                continue
            payload = {
                "name": r.get("name", "role"),
                "permissions": str(r.get("permissions", 0)),
                "mentionable": r.get("mentionable", False),
                "hoist": r.get("hoist", False)
            }
            try:
                new_role = bot_api_post(f"/guilds/{guild_id}/roles", payload)
                created["roles"].append(new_role)
            except Exception as e:
                # best-effort: continue and capture error
                created.setdefault("role_errors", []).append({"role": r.get("name"), "error": str(e)})

        # restore channels (categories & their children)
        # We'll create categories first, then other channels with parent
        # Map old category ids to new category ids using names
        category_map = {}
        for ch in snapshot.get("channels", []):
            if ch.get("type") == 4:  # CATEGORY
                payload = {"name": ch.get("name", "category"), "type": 4}
                try:
                    nc = bot_api_post(f"/guilds/{guild_id}/channels", payload)
                    category_map[ch.get("id")] = nc.get("id")
                    created["channels"].append(nc)
                except Exception as e:
                    created.setdefault("channel_errors", []).append({"channel": ch.get("name"), "error": str(e)})

        # now other channels
        for ch in snapshot.get("channels", []):
            if ch.get("type") == 4:
                continue
            payload = {
                "name": ch.get("name", "channel"),
                "type": ch.get("type", 0),
                "topic": ch.get("topic", ""),
                "nsfw": ch.get("nsfw", False)
            }
            parent_id = ch.get("parent_id")
            if parent_id:
                new_parent = category_map.get(parent_id)
                if new_parent:
                    payload["parent_id"] = new_parent
            try:
                nc = bot_api_post(f"/guilds/{guild_id}/channels", payload)
                created["channels"].append(nc)
            except Exception as e:
                created.setdefault("channel_errors", []).append({"channel": ch.get("name"), "error": str(e)})

    except Exception as e:
        return jsonify({"error": "restore failed during operations", "details": str(e), "partial": created}), 500

    return jsonify({"ok": True, "created": created})

# ---------- Auto-translate endpoint (Libre default) ----------
@app.route("/api/translate", methods=["POST"])
@require_auth
def translate():
    """
    payload: {text: str, target: 'en'|'fr'...}
    """
    body = request.json or {}
    text = body.get("text", "")
    target = body.get("target", "en")
    if not text:
        return jsonify({"error": "no text provided"}), 400

    provider = TRANSLATE_PROVIDER.lower()
    if provider == "libre" and TRANSLATOR_AVAILABLE:
        try:
            translated = LibreTranslator(source="auto", target=target).translate(text)
            return jsonify({"translated": translated})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif provider == "google" and GOOGLE_API_KEY:
        url = f"https://translation.googleapis.com/language/translate/v2?key={GOOGLE_API_KEY}"
        resp = requests.post(url, json={"q": text, "target": target})
        return jsonify(resp.json())
    elif provider == "deepl" and DEEPL_API_KEY:
        url = "https://api-free.deepl.com/v2/translate"
        resp = requests.post(url, data={"auth_key": DEEPL_API_KEY, "text": text, "target_lang": target.upper()})
        return jsonify(resp.json())
    else:
        return jsonify({"error": "no translator configured or missing API key"}), 500

# ---------- Suspicious account checker helper ----------
@app.route("/api/check_account", methods=["POST"])
@require_auth
def check_account():
    """
    Accepts: {user: {id, created_at (isotime or unix), avatar_url, username}}
    Returns: {risk_score: int, reasons: [...]}
    """
    body = request.json or {}
    user = body.get("user") or {}
    reasons = []
    score = 0
    # Age check (support unix timestamp or ISO numeric)
    created = user.get("created_at")
    if created:
        try:
            created_ts = float(created)
            age_seconds = time.time() - created_ts
            if age_seconds < 60 * 60 * 24 * 7:  # < 7 days
                reasons.append("Account < 7 days old")
                score += 40
        except Exception:
            pass
    avatar = user.get("avatar_url") or ""
    if not avatar:
        reasons.append("No avatar")
        score += 20
    username = user.get("username", "")
    if username and len(username) < 3:
        reasons.append("Short username")
        score += 10
    # placeholder: add other heuristics as needed
    return jsonify({"risk_score": score, "reasons": reasons})

# ---------- Simple health check ----------
@app.route("/health")
def health():
    return jsonify({"ok": True})

# ---------- Local file download for backup (optional) ----------
@app.route("/api/guilds/<guild_id>/backup/download")
@require_auth
def download_backup(guild_id):
    local = os.path.join(BACKUP_FOLDER, f"{guild_id}.json")
    if os.path.exists(local):
        return send_file(local, as_attachment=True)
    sb = get_backup_from_supabase(guild_id)
    if sb:
        # return the JSON payload
        return jsonify(sb)
    return jsonify({"error": "no backup found"}), 404

# ---------- Run Flask dev (for local testing) ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("Starting backend on port", port)
    app.run(host="0.0.0.0", port=port)
