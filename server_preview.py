"""Local browser preview backed by the real Game simulation (no Ursina).

Runs the authoritative Game loop at 60 Hz in a background thread and serves
its state over a tiny stdlib HTTP server. The browser page only renders
what the server sends and forwards key state back - the simulation stays
the single source of truth, same as the headless contract runner.

Usage:
  python server_preview.py [--port 8787] [--night 1]
Then open http://localhost:8787/ in a browser.
"""
import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from simulation import Game

ROOT = Path(__file__).parent
PAGES = {'/': 'web3d.html', '/index.html': 'web3d.html', '/3d': 'web3d.html', '/2d': 'preview.html'}


class GameServer:
    def __init__(self, night=1, seed=1):
        self.lock = threading.Lock()
        self.night = night
        self.seed = seed
        self.game = Game(seed=seed, night=night)
        self.running = True

    def reset(self, night=None):
        with self.lock:
            if night is not None:
                self.night = night
            self.game = Game(seed=self.seed, night=self.night)

    def set_input(self, keys):
        with self.lock:
            g = self.game
            mx = max(-1.0, min(1.0, float(keys.get('x', 0))))
            mz = max(-1.0, min(1.0, float(keys.get('z', 0))))
            g.input['move'] = [mx, mz]
            g.input['cam_yaw_deg'] = float(keys.get('yaw', 0))
            for k in ('jump', 'dash', 'interact', 'pulse', 'pause'):
                if k in keys:
                    g.input[k] = bool(keys[k])

    def snapshot(self):
        with self.lock:
            return self.game.snapshot()

    def loop(self):
        tick_dt = 1 / 60
        next_t = time.perf_counter()
        while self.running:
            next_t += tick_dt
            with self.lock:
                if self.game.state in ('playing', 'paused'):
                    self.game.step()
            sleep_for = next_t - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                next_t = time.perf_counter()


def make_handler(server: GameServer):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # keep stdout quiet; errors still raise

        def _send(self, status, body: bytes, content_type='application/json'):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split('?', 1)[0]
            if path in PAGES:
                body = (ROOT / PAGES[path]).read_bytes()
                self._send(200, body, 'text/html; charset=utf-8')
            elif path == '/api/state':
                body = json.dumps(server.snapshot()).encode('utf-8')
                self._send(200, body)
            elif path == '/api/leaderboard':
                import leaderboard
                self._send(200, json.dumps({'entries': leaderboard.load()}, ensure_ascii=False).encode('utf-8'))
            else:
                self._send(404, b'{"error":"not found"}')

        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length) if length else b'{}'
            try:
                data = json.loads(raw or b'{}')
            except json.JSONDecodeError:
                data = {}
            if self.path == '/api/input':
                server.set_input(data)
                self._send(200, b'{"ok":true}')
            elif self.path == '/api/reset':
                night = data.get('night')
                server.reset(night=int(night) if night else None)
                self._send(200, b'{"ok":true}')
            elif self.path == '/api/leaderboard':
                import leaderboard
                try:
                    entries = leaderboard.add(data.get('name', ''), data.get('score', 0), data.get('nights_won', 0), server.seed)
                    self._send(200, json.dumps({'entries': entries}, ensure_ascii=False).encode('utf-8'))
                except (ValueError, TypeError) as e:
                    self._send(400, json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))
            else:
                self._send(404, b'{"error":"not found"}')

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

    return Handler


def serve(port=8787, night=1, seed=1, host='127.0.0.1', open_browser=False):
    server = GameServer(night=night, seed=seed)
    sim_thread = threading.Thread(target=server.loop, daemon=True)
    sim_thread.start()

    httpd = ThreadingHTTPServer((host, port), make_handler(server))
    url = f'http://localhost:{port}/'
    print(f'Dao Den Long running at {url}  (Ctrl+C to stop)')
    if open_browser:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.running = False
        httpd.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8787)
    ap.add_argument('--night', type=int, default=1, choices=(1, 2, 3))
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--host', default='127.0.0.1', help='use 0.0.0.0 inside Docker')
    a = ap.parse_args()
    serve(a.port, a.night, a.seed, a.host)


if __name__ == '__main__':
    main()
