"""Small playable Ursina presentation backed by the same Game simulation."""
def launch():
    try:
        from ursina import Ursina, Entity, Text, color, camera, held_keys, Vec3
    except ImportError:
        raise SystemExit('Install dependencies first: python3 -m pip install -r requirements.txt')
    from simulation import Game
    app=Ursina(); game=Game(); entities=[]
    Entity(model='plane', scale=44, texture='white_cube', texture_scale=(44,44), color=color.rgb(24,18,42))
    Entity(model='circle', scale=38, y=.01, rotation_x=90, color=color.rgb(40,28,56))
    player=Entity(model='cube', color=color.rgb(245,190,95), scale=(.8,1.6,.8), y=.8)
    Entity(model='cone', color=color.rgb(215,110,55), scale=(1.3,.7,1.3), y=1.9, parent=player)
    hud=Text('', origin=(-.5,.5), x=-.86, y=.45, scale=1.1)
    Text('WASD move   E light   SPACE pulse   R restart', origin=(0,0), y=-.46, color=color.rgb(240,210,170))
    def rebuild():
        nonlocal entities
        for e in entities: e.disable()
        entities=[]
        for m in game.motes: entities.append(Entity(model='sphere', color=color.yellow, scale=.3, position=(m['pos'][0],.35,m['pos'][2])))
        for l in game.lanterns: entities.append(Entity(model='cube', color=color.orange if l['lit'] else color.rgb(80,55,80), scale=(.5,2,.5), y=1, position=(l['pos'][0],0,l['pos'][2])))
        for s in game.shades: entities.append(Entity(model='sphere', color=color.rgb(80,25,100), scale=1, position=(s['pos'][0],.7,s['pos'][2])))
    def input(key):
        if key=='e': game.input['interact']=True
        if key=='space': game.input['pulse']=True
        if key=='r' and game.state!='playing': game.__init__(); rebuild()
    def update():
        game.input['move']=[held_keys['d']-held_keys['a'], held_keys['w']-held_keys['s']]
        game.step(); player.position=Vec3(*game.player); player.y=.8
        camera.position=player.position+Vec3(0,14,-18); camera.look_at(player)
        hud.text=f'ĐÊM 1 • ĐIỂM {game.score}\nĐom đóm {game.carried}/5   Lửa {game.flames}/3\nĐèn sáng {sum(l["lit"] for l in game.lanterns)}/5'
        if game.tick%6==0: rebuild()
        game.input['interact']=False; game.input['pulse']=False
        if game.state!='playing': hud.text += f'\n\n{("THẮNG!" if game.state=="won" else "THUA!")}  Nhấn R để chơi lại'
    rebuild(); app.run()
