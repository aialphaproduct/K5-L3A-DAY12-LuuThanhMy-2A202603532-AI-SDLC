import argparse
import json
import sys
from simulation import run_headless

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--headless', action='store_true')
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--night', type=int, default=1)
    p.add_argument('--scenario')
    p.add_argument('--inputs')
    p.add_argument('--ticks', type=int, default=18000)
    p.add_argument('--out', default='-')
    p.add_argument('--snapshot-every', type=int, default=10)
    a = p.parse_args()
    if a.night != 1 or a.ticks < 0 or a.snapshot_every < 1:
        print('invalid night, ticks, or snapshot interval', file=sys.stderr); return 2
    if a.headless:
        try:
            lines = run_headless(a.seed, a.ticks, a.snapshot_every, a.scenario, a.inputs)
            if a.out == '-':
                print('\n'.join(lines))
            else:
                with open(a.out, 'w', encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
            return 0
        except (ValueError, OSError, json.JSONDecodeError) as e:
            print(str(e), file=sys.stderr); return 2
    from visual import launch
    launch()

if __name__ == '__main__': main()
