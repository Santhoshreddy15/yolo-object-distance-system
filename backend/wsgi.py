import os
import sys
from pathlib import Path

# Load .env file from project root before anything else
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.is_file():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.config import Config

# Primary WSGI entry point instances for production servers (Waitress, Gunicorn, uWSGI)
app = create_app(Config)
application = app

# Pre-warm model cache in background/startup so worker threads don't lock on first request
try:
    with app.app_context():
        from backend.routes.api import get_detector
        _warmed_detector = get_detector()
        if _warmed_detector.is_loaded:
            print(f"[WSGI] YOLO model pre-warmed successfully: {_warmed_detector.model_name}")
        else:
            print(f"[WSGI] YOLO model initialized in fallback mode: {_warmed_detector.load_error}")
except Exception as _e:
    print(f"[WSGI] Warning during YOLO model pre-warm: {_e}")

def run_server(host=None, port=None, threads=None):
    """
    Run multi-threaded WSGI server with graceful fallbacks:
    1. waitress (Windows & Linux multi-threaded production server)
    2. werkzeug.serving.run_simple (threaded=True)
    3. Python standard library wsgiref with ThreadingMixIn
    """
    host = host or os.environ.get("HOST", "127.0.0.1")
    port = int(port or os.environ.get("PORT", "5000"))
    threads = int(threads or os.environ.get("THREADS", "16"))

    # Attempt 1: Waitress
    try:
        from waitress import serve
        print(f"[WSGI] Starting Waitress production server on http://{host}:{port} with {threads} threads...")
        serve(app, host=host, port=port, threads=threads)
        return
    except ImportError:
        pass

    # Attempt 2: Werkzeug threaded server
    try:
        from werkzeug.serving import run_simple
        print(f"[WSGI] Waitress not found; starting Werkzeug multi-threaded server on http://{host}:{port}...")
        run_simple(host, port, app, threaded=True, use_reloader=False)
        return
    except (ImportError, Exception):
        pass

    # Attempt 3: Pure Python standard library Threading WSGI Server
    try:
        from socketserver import ThreadingMixIn
        from wsgiref.simple_server import WSGIServer, make_server

        class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
            daemon_threads = True
            allow_reuse_address = True

        print(f"[WSGI] Starting standard library ThreadingWSGIServer on http://{host}:{port}...")
        httpd = make_server(host, port, app, server_class=ThreadingWSGIServer)
        httpd.serve_forever()
    except Exception as e:
        print(f"[WSGI] Fatal: Failed to start multi-threaded WSGI server: {e}")
        # Last resort fallback: Flask built-in run
        app.run(host=host, port=port, threaded=True)

if __name__ == "__main__":
    run_server()
