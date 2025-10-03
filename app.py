import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, current_app, send_from_directory,
    redirect, url_for, flash
)
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import validators

load_dotenv()

required_vars = ["NASA_API_KEY", "FLASK_SECRET_KEY"]

for var in required_vars:
    if not os.getenv(var):
        sys.stderr.write(f"[ERROR] Missing required environment variable: {var}\n")
        sys.exit(1)

NASA_API_KEY = os.environ["NASA_API_KEY"]
SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
CACHE_DIR = os.environ.get("CACHE_DIR", "static/cache")
try:
    CACHE_TIMEOUT = int(os.environ.get("CACHE_TIMEOUT", "86400"))
except ValueError:
    CACHE_TIMEOUT = 86400

Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")

app.config.update(
    SECRET_KEY=SECRET_KEY,
    CACHE_TYPE="SimpleCache",
    CACHE_DEFAULT_TIMEOUT=CACHE_TIMEOUT,
)

Talisman(app, content_security_policy={
    'default-src': "'self'",
    'img-src': ["'self'", 'https://apod.nasa.gov', 'https://*.nasa.gov', 'data:'],
    'script-src': ["'self'"],
    'style-src': ["'self'", "'unsafe-inline'"],
})

limiter = Limiter(app, key_func=get_remote_address, default_limits=["60 per minute"])

cache = Cache(app)

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.3, status_forcelist=(500, 502, 504))
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)
session.mount('http://', adapter)

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

def safe_date_input(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        if dt < datetime(1995, 6, 16).date() or dt > datetime.now().date():
            return ""
        return dt.isoformat()
    except ValueError:
        return ""

@cache.cached(timeout=3600, query_string=True)
@limiter.limit("10 per minute")
@app.route('/', methods=['GET'])
def index():
    date = safe_date_input(request.args.get('date', ''))
    payload = {
        'api_key': NASA_API_KEY,
        'hd': True
    }
    if date:
        payload['date'] = date

    try:
        resp = session.get(NASA_APOD_URL, params=payload, timeout=6)
        resp.raise_for_status()
    except requests.RequestException:
        current_app.logger.exception('Failed requesting NASA APOD')
        flash('Failed to contact NASA APOD service. Please try again later.', 'error')
        return render_template('index.html', apod=None)

    data = resp.json()
    media_type = data.get('media_type')

    result = {
        'title': data.get('title'),
        'date': data.get('date'),
        'explanation': data.get('explanation'),
        'media_type': media_type,
        'url': data.get('url'),
        'hdurl': data.get('hdurl')
    }

    if media_type == 'image':
        remote_url = data.get('hdurl') or data.get('url')
        if remote_url and remote_url.strip():
            try:
                extension_part = remote_url.split('.')[-1]
                ext = extension_part.split('?')[0].lower()
                if len(ext) > 5 or not ext.isalnum():
                    ext = 'jpg' if 'jpg' in ext else 'png' if 'png' in ext else 'gif' if 'gif' in ext else 'mp4' if 'mp4' in ext else 'jpeg' if 'jpeg' in ext else 'unknown'

                filename = f"apod_{result['date']}.{ext}"
                filepath = os.path.join(CACHE_DIR, filename)

                if not os.path.exists(filepath):
                    try:
                        r = session.get(remote_url, stream=True, timeout=10)
                        r.raise_for_status()
                        with open(filepath, 'wb') as f:
                            for chunk in r.iter_content(1024 * 8):
                                f.write(chunk)
                        result['local_url'] = url_for('cached_file', filename=filename)
                    except requests.RequestException:
                        current_app.logger.exception('Failed to cache remote image')
                        result['local_url'] = remote_url
                    except IOError:
                        current_app.logger.exception(f'Failed to write cached image file: {filepath}')
                        result['local_url'] = remote_url
                else:
                    result['local_url'] = url_for('cached_file', filename=filename)

            except Exception as e:
                current_app.logger.error(f"Error during image caching: {e}")
                result['local_url'] = remote_url
        else:
            result['local_url'] = remote_url

    return render_template('index.html', apod=result)

@limiter.exempt
@app.route(f'/{CACHE_DIR}/<path:filename>')
def cached_file(filename):
    if '..' in filename or filename.startswith('/'):
        return '', 400
    return send_from_directory(CACHE_DIR, filename)

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template(
        'index.html', apod=None, error='Rate limit exceeded. Please try again later.'
    ), 429

if __name__ == '__main__':
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        ssl_context=('cert.pem', 'key.pem')  # Enable HTTPS
    )
