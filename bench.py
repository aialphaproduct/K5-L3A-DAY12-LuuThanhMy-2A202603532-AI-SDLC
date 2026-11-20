"""Ticket-04 benchmark: standard Night 1 scene in a 1280x720 Ursina window, vsync off.

200 wander shades, 100 motes, L1-L3 lit at fuel 100, the player standing at the origin.
The camera orbits the origin at radius 30 m and Y = 15 m, starting at (30, 15, 0), going
counter-clockwise seen from above, one lap every 15 s. The first 3 s are warm-up; then exactly
`duration` seconds of frames are measured, bench.json is written, and the process exits 0.
"""
import gc
import json
import math
import os
import sys
import time

PROCESS_T0 = time.perf_counter()  # earliest point we control: set when main.py imports this module


def run(seed=42, duration=30.0, out='bench.json'):
    from panda3d.core import loadPrcFileData
    loadPrcFileData('', 'sync-video #f')     # vsync off at the Panda3D level too
    loadPrcFileData('', 'clock-mode normal') # no frame-rate cap
    from ursina import Ursina, Entity, Cylinder, camera, color, application, window
    from ursina import time as utime
    from ursina.lights import DirectionalLight, AmbientLight
    from ursina.shaders import lit_with_shadows_shader
    from panda3d.core import PandaSystem
    import ursina
    from simulation import bench_game
    from perf import rss_mb, os_label

    app = Ursina(title='Dao Den Long - bench', size=(1280, 720), borderless=False, fullscreen=False,
                 vsync=False, development_mode=False, editor_ui_enabled=False)
    window.color = color.hex('#0E1430')
    game = bench_game(seed)

    # same look as play: lit shader, moon light with shadows, ambient that follows lantern progress
    lit_count = sum(1 for l in game.lanterns if l['lit'])
    sun = DirectionalLight(shadows=True); sun.look_at((1, -1.5, 0.6)); sun.color = color.hex('#b8c4ff')
    AmbientLight(color=color.rgba(0.15 + 0.55 * lit_count / len(game.lanterns), 0.2, 0.35, 1))
    Entity(model=Cylinder(64), scale=(80, 0.6, 80), y=-0.6, color=color.hex('#2F5D50'), shader=lit_with_shadows_shader)
    Entity(model='plane', scale=800, y=-8, color=color.hex('#12384A'))
    for l in game.lanterns:
        Entity(model='cube', scale=(.25, 3, .25), position=(l['pos'][0], 1.5, l['pos'][2]), color=color.hex('#6B4A2F'), shader=lit_with_shadows_shader)
        Entity(model='sphere', scale=.9, position=(l['pos'][0] + .8, 2.35, l['pos'][2]),
               color=color.hex('#FFB347') if l['lit'] else color.hex('#5B5F6E'), unlit=l['lit'])
    Entity(model='cube', scale=(.8, 1.6, .8), y=.8, color=color.hex('#E8E2D0'), shader=lit_with_shadows_shader)
    # shade body tinted toward the #7A3CFF rim (one draw call per shade instead of body + rim shell)
    shades = [Entity(model='sphere', scale=(1.4, 1.7, 1.4), color=color.hex('#2a1640'), shader=lit_with_shadows_shader) for _ in game.shades]
    # motes do not move in the bench scene (pickup is off), so merge all 100 into a single mesh
    mote_root = Entity()
    for m in game.motes:
        Entity(parent=mote_root, model='sphere', scale=.25, position=(m['pos'][0], .6, m['pos'][2]))
    mote_root.combine(); mote_root.color = color.hex('#FFF6C2'); mote_root.unlit = True

    state = {'t_start': None, 'last': None, 'dts': [], 'acc': 0.0, 'peak': 0.0, 'load_ms': None, 'frame': 0}

    def update():
        now = time.perf_counter()
        if state['load_ms'] is None:
            state['load_ms'] = round((now - PROCESS_T0) * 1000)
            state['t_start'] = now
        # fixed 60 Hz simulation, decoupled from the render rate
        state['acc'] += min(utime.dt, 0.25)
        while state['acc'] >= 1 / 60:
            game.step(); state['acc'] -= 1 / 60
        for e, s in zip(shades, game.shades):
            e.x, e.y, e.z = s['pos'][0], 1.1, s['pos'][2]
        t = now - state['t_start']
        a = 2 * math.pi * t / 15.0
        camera.position = (30 * math.cos(a), 15, 30 * math.sin(a))
        camera.look_at((0, 0, 0))
        if t >= 3.0:
            if state['last'] is None:
                # measurement starts: freeze what is already allocated and stop the cyclic GC so a
                # collection pause does not land inside the measured window (refcounting still frees memory)
                gc.collect(); gc.freeze(); gc.disable()
            if state['last'] is not None:
                state['dts'].append((now - state['last']) * 1000)
            state['last'] = now
            state['frame'] += 1
            if state['frame'] % 15 == 0:
                state['peak'] = max(state['peak'], rss_mb())
            if t >= 3.0 + duration:
                finish()

    def finish():
        dts = state['dts']
        n = len(dts)
        worst = sorted(dts, reverse=True)[:max(1, math.ceil(0.01 * n))]
        p95 = sorted(dts)[min(n - 1, math.ceil(0.95 * n) - 1)]
        gsg = app.win.getGsg()
        report = {
            'contract_version': '1.3',
            'avg_fps': round(1000 * n / sum(dts), 1),
            'p1_low_fps': round(1000 / (sum(worst) / len(worst)), 1),
            'frame_ms_p95': round(p95, 2),
            'frames': n,
            'load_ms': state['load_ms'],
            'peak_mem_mb': round(max(state['peak'], rss_mb()), 1),
            'vsync_off': True,
            'renderer': f"Ursina {getattr(ursina, '__version__', '7')} / Panda3D {PandaSystem.getVersionString()} / {gsg.getDriverRenderer()}",
            'os': os_label(),
        }
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report))
        sys.stdout.flush()
        os._exit(0)

    Entity(update=update)
    app.run()
