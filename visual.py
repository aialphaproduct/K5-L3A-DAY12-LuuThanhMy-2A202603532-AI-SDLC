"""Small playable Ursina presentation backed by the same Game simulation.

Visual-only: no gameplay numbers here affect the simulation contract.
Entities are pooled by id and updated every frame instead of being torn down
and rebuilt every few ticks, which used to leak Entities (only .disable()'d,
never destroyed) and made the game slow down and eventually freeze.
"""
import math


def launch():
    try:
        from ursina import (Ursina, Entity, Text, color, camera, held_keys,
                             Vec3, destroy, time as ursina_time)
    except ImportError:
        raise SystemExit('Install dependencies first: python3 -m pip install -r requirements.txt')
    from simulation import Game

    app = Ursina()
    game = Game()
    clock = {'t': 0.0}

    Entity(model='plane', scale=44, texture='white_cube', texture_scale=(44, 44), color=color.rgb(24, 18, 42))
    Entity(model='circle', scale=38, y=.01, rotation_x=90, color=color.rgb(40, 28, 56))
    player = Entity(model='cube', color=color.rgb(245, 190, 95), scale=(.8, 1.6, .8), y=.8)
    Entity(model='cone', color=color.rgb(215, 110, 55), scale=(1.3, .7, 1.3), y=1.9, parent=player)
    hud = Text('', origin=(-.5, .5), x=-.86, y=.45, scale=1.1)
    Text('WASD move   E light   SPACE pulse   R restart', origin=(0, 0), y=-.46, color=color.rgb(240, 210, 170))

    pools = {'mote': {}, 'lantern': {}, 'shade': {}, 'drifter': {}, 'charm': {}}
    pulse_rings = []

    def sync_pool(kind, items, make):
        pool = pools[kind]
        seen = set()
        for it in items:
            seen.add(it['id'])
            ent = pool.get(it['id'])
            if ent is None:
                ent = make(it)
                pool[it['id']] = ent
            ent._data = it
        for stale_id in [k for k in pool if k not in seen]:
            destroy(pool.pop(stale_id))

    def make_mote(m):
        return Entity(model='sphere', color=color.yellow, scale=.3)

    def make_lantern(l):
        return Entity(model='cube', scale=(.5, 2, .5), y=1)

    def make_shade(s):
        return Entity(model='sphere', scale=1)

    def make_drifter(d):
        return Entity(model='diamond' if _has_model('diamond') else 'sphere', color=color.rgb(150, 60, 150), scale=.9)

    def make_charm(c):
        return Entity(model='sphere', color=color.rgb(120, 220, 255), scale=.5)

    def _has_model(name):
        return True  # ursina falls back silently; kept for readability

    def reset():
        for pool in pools.values():
            for ent in list(pool.values()):
                destroy(ent)
            pool.clear()
        for r in pulse_rings:
            destroy(r)
        pulse_rings.clear()

    def input(key):
        if key == 'e':
            game.input['interact'] = True
        if key == 'space':
            game.input['pulse'] = True
        if key == 'r' and game.state != 'playing':
            reset()
            game.__init__()

    def spawn_pulse_ring():
        ring = Entity(model='circle', rotation_x=90, color=color.rgba(255, 225, 150, 160),
                       scale=.6, position=player.position + Vec3(0, .1, 0))
        ring._age = 0.0
        pulse_rings.append(ring)

    def update():
        dt = ursina_time.dt
        clock['t'] += dt
        was_pulse = game.input.get('pulse', False)
        game.input['move'] = [held_keys['d'] - held_keys['a'], held_keys['w'] - held_keys['s']]
        game.step()

        # Smooth-follow player instead of snapping, and face the move direction.
        target = Vec3(game.player[0], .8, game.player[2])
        player.position = Vec3(*[player.position[i] + (target[i] - player.position[i]) * min(1, dt * 14) for i in range(3)])
        player.y += math.sin(clock['t'] * 10) * 0.02  # idle bob, purely cosmetic
        fx, fz = game.face
        if abs(fx) + abs(fz) > .01:
            player.rotation_y = math.degrees(math.atan2(fx, fz))

        cam_target = player.position + Vec3(0, 11, -14)
        camera.position = Vec3(*[camera.position[i] + (cam_target[i] - camera.position[i]) * min(1, dt * 8) for i in range(3)])
        camera.look_at(player)

        if not was_pulse and game.input.get('pulse'):
            spawn_pulse_ring()

        sync_pool('mote', game.motes, make_mote)
        for m in game.motes:
            e = pools['mote'][m['id']]
            e.position = (m['pos'][0], .35 + math.sin(clock['t'] * 4 + hash(m['id']) % 10) * .08, m['pos'][2])

        sync_pool('lantern', game.lanterns, make_lantern)
        for l in game.lanterns:
            e = pools['lantern'][l['id']]
            e.position = (l['pos'][0], l['pos'][1] if len(l['pos']) > 1 else 0, l['pos'][2])
            e.color = color.orange if l['lit'] else color.rgb(80, 55, 80)
            e.scale_y = 2 + (math.sin(clock['t'] * 6) * .08 if l['lit'] else 0)

        sync_pool('shade', game.shades, make_shade)
        for s in game.shades:
            e = pools['shade'][s['id']]
            e.position = (s['pos'][0], .7, s['pos'][2])
            e.color = color.rgb(90, 180, 255) if s['state'] == 'stunned' else color.rgb(80, 25, 100)
            e.scale = 1.3 if s['state'] == 'spawning' else 1.0

        sync_pool('drifter', getattr(game, 'drifters', []), make_drifter)
        for d in getattr(game, 'drifters', []):
            e = pools['drifter'][d['id']]
            e.position = (d['pos'][0], .6, d['pos'][2])

        sync_pool('charm', getattr(game, 'charms', []), make_charm)
        for c in getattr(game, 'charms', []):
            e = pools['charm'][c['id']]
            e.enabled = c.get('available', True)
            e.position = (c['pos'][0], .5, c['pos'][2])

        for r in pulse_rings[:]:
            r._age += dt
            r.scale = .6 + r._age * 18
            r.color = color.rgba(255, 225, 150, max(0, 160 - int(r._age * 400)))
            if r._age > .4:
                pulse_rings.remove(r)
                destroy(r)

        game.input['interact'] = False
        game.input['pulse'] = False

        night_label = f'ĐÊM {game.night}'
        hud.text = (f'{night_label} • ĐIỂM {game.score}\n'
                    f'Đom đóm {game.carried}/10   Lửa {game.flames}/3\n'
                    f'Đèn sáng {sum(l["lit"] for l in game.lanterns)}/{len(game.lanterns)}')
        if game.state != 'playing':
            hud.text += f'\n\n{("THẮNG!" if game.state == "won" else "THUA!")}  Nhấn R để chơi lại'

    app.run()
