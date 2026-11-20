import argparse
import json
import sys

import bench  # sets the process start timestamp used for bench load_ms; imports nothing heavy
from simulation import run_headless


def main():
    p = argparse.ArgumentParser(description='Dao Den Long')
    p.add_argument('--headless', action='store_true', help='run the Test Contract headless simulation')
    p.add_argument('--bench', action='store_true', help='Ticket-04 benchmark scene (1280x720 window)')
    p.add_argument('--soak', action='store_true', help='Ticket-04 soak test (headless, several nights)')
    p.add_argument('--export-leaderboard', metavar='FILE', help='write the local leaderboard to FILE')
    p.add_argument('--native', action='store_true', help='open the Ursina desktop client instead of the web game')
    p.add_argument('--port', type=int, default=8787)
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--night', type=int, default=1)
    p.add_argument('--scenario')
    p.add_argument('--inputs')
    p.add_argument('--ticks', type=int, default=18000)
    p.add_argument('--out', default=None)
    p.add_argument('--snapshot-every', type=int, default=10)
    p.add_argument('--duration', type=float, default=30.0)
    p.add_argument('--nights', type=int, default=10)
    a = p.parse_args()
    if a.night not in (1, 2, 3) or a.ticks < 0 or a.snapshot_every < 1 or a.duration <= 0 or a.nights < 1:
        print('invalid night, ticks, snapshot interval, duration or nights', file=sys.stderr); return 2

    if a.export_leaderboard:
        import leaderboard
        try:
            leaderboard.export(a.export_leaderboard); return 0
        except OSError as e:
            print(str(e), file=sys.stderr); return 1
    if a.soak:
        from perf import soak
        r = soak(7 if a.seed is None else a.seed, a.nights, a.out or 'soak.json')
        print(json.dumps(r)); return 0 if r['crashes'] == 0 else 1
    if a.bench:
        bench.run(42 if a.seed is None else a.seed, a.duration, a.out or 'bench.json'); return 0
    if a.headless:
        try:
            lines = run_headless(1 if a.seed is None else a.seed, a.ticks, a.snapshot_every, a.scenario, a.inputs, a.night)
            if a.out in (None, '-'):
                print('\n'.join(lines))
            else:
                with open(a.out, 'w', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
            return 0
        except (ValueError, OSError, json.JSONDecodeError) as e:
            print(str(e), file=sys.stderr); return 2
    if a.native:
        from visual import launch
        launch(); return 0
    import server_preview
    server_preview.serve(port=a.port, night=a.night, seed=1 if a.seed is None else a.seed, open_browser=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
