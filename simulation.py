import json, math, random

SPEED=6.0; CAP=5; COST=5; PICKUP=1.4; INTERACT=2.0; PULSE_COST=1
PULSE_RADIUS=6.0; DURATION=300; INVULN=90; STUN=120; PUSH=2.0
SHADE_SPEED=2.0; HIT=1.0; SAFE=3.0

def dist(a,b): return math.hypot(a[0]-b[0],a[2]-b[2])
def load_json(path, default):
    if not path: return default
    with open(path,encoding='utf-8') as f: return json.load(f)

class Game:
    def __init__(self, seed=1, scenario=None):
        self.rng=random.Random(seed); self.tick=0; self.time=300*60; self.score=0
        self.state='playing'; self.flames=3; self.carried=0; self.invuln=0; self.last_pulse=-9999
        self.player=[0.,0.,0.]; self.input={'move':[0,0],'cam_yaw_deg':0,'jump':False,'interact':False,'pulse':False}
        self.prev={k:False for k in ('jump','interact','pulse')}; self.events=[]
        self.lanterns=[{'id':f'L{i+1}','pos':[20*math.cos(i*2*math.pi/5),0,20*math.sin(i*2*math.pi/5)],'lit':False,'deposited':0} for i in range(5)]
        self.motes=[{'id':f'M{i+1}','pos':[8*math.cos(i*2*math.pi/20),0,8*math.sin(i*2*math.pi/20)]} for i in range(20)]
        self.shades=[{'id':'S1','pos':[10.,0.,0.],'state':'chase','stun':0}]
        if scenario:
            p=scenario.get('player',{}); self.player=list(map(float,p.get('pos',[0,0,0]))); self.carried=int(p.get('carried',0)); self.flames=int(p.get('flames',3))
            if 'motes' in scenario:self.motes=[{'id':f'M{i+1}','pos':list(map(float,x))} for i,x in enumerate(scenario['motes'])]
            if 'shades' in scenario:self.shades=[{'id':x.get('id',f'S{i+1}'),'pos':list(map(float,x['pos'])),'state':'chase','stun':0} for i,x in enumerate(scenario['shades'])]
            for x in scenario.get('lanterns',[]):
                l=next((l for l in self.lanterns if l['id']==x.get('id')),None)
                if l:
                    l['pos']=list(map(float,x.get('pos',l['pos']))); l['deposited']=int(x.get('deposited',l['deposited'])); l['lit']=bool(x.get('lit',l['deposited']>=COST))
            self.time=int(float(scenario.get('time_left_s',300))*60)
            if scenario.get('random_motes',True): self.motes += [{'id':f'R{i}','pos':[self.rng.uniform(-18,18),0,self.rng.uniform(-18,18)]} for i in range(20)]
            if scenario.get('random_shades',True): pass
    def event(self,n,d): self.events.append({'type':'event','tick':self.tick,'name':n,'data':d})
    def step(self):
        if self.state!='playing': return
        k=self.tick; self.tick+=1; self.time-=1
        inp=self.input; x,z=inp['move']; mag=math.hypot(x,z)
        if mag>1:x,z=x/mag,z/mag
        th=math.radians(inp['cam_yaw_deg']); dx=x*math.cos(th)+z*math.sin(th); dz=-x*math.sin(th)+z*math.cos(th)
        self.player[0]+=dx*SPEED/60; self.player[2]+=dz*SPEED/60
        for key in self.prev:
            pressed=inp[key] and not self.prev[key]; self.prev[key]=inp[key]
            if pressed and key=='pulse' and self.carried>=PULSE_COST and k-self.last_pulse>=60:
                self.carried-=PULSE_COST; self.last_pulse=k; ids=[]
                for s in self.shades:
                    if dist(s['pos'],self.player)<=PULSE_RADIUS:
                        s['state']='stunned'; s['stun']=STUN; ids.append(s['id']); self.score+=25
                        vx=s['pos'][0]-self.player[0]; vz=s['pos'][2]-self.player[2]; d=math.hypot(vx,vz) or 1; s['pos'][0]+=vx/d*PUSH; s['pos'][2]+=vz/d*PUSH
                self.event('pulse',{'stunned_ids':ids})
            if pressed and key=='interact':
                for l in self.lanterns:
                    if dist(l['pos'],self.player)<=INTERACT and self.carried:
                        amount=min(self.carried,COST-l['deposited']); l['deposited']+=amount; self.carried-=amount; self.score+=amount*10
                        self.event('deposit',{'lantern_id':l['id'],'amount':amount,'deposited':l['deposited']})
                        if l['deposited']>=COST and not l['lit']:
                            l['lit']=True; self.score+=100; self.event('lantern_lit',{'lantern_id':l['id']})
                        break
        for m in self.motes[:]:
            if self.carried<CAP and dist(m['pos'],self.player)<=PICKUP:
                self.motes.remove(m); self.carried+=1; self.score+=10; self.event('mote_picked',{'carried':self.carried})
        for s in self.shades:
            if s['stun']>0:s['stun']-=1
            else:
                s['state']='chase'; nearest=min(self.lanterns,key=lambda l:dist(l['pos'],s['pos']))
                target=self.player if dist(s['pos'],self.player)<dist(nearest['pos'],self.player) else self.player
                d=dist(s['pos'],target)
                if d>0:s['pos'][0]+=(target[0]-s['pos'][0])/d*SHADE_SPEED/60; s['pos'][2]+=(target[2]-s['pos'][2])/d*SHADE_SPEED/60
                if self.invuln==0 and d<=HIT:
                    self.flames-=1; dropped=self.carried//2; self.carried-=dropped; self.invuln=90
                    self.event('player_hit',{'by':'shade','flames':self.flames,'dropped':dropped})
                    for i in range(dropped): self.motes.append({'id':f'D{self.tick}-{i}','pos':self.player.copy()})
        self.invuln=max(0,self.invuln-1)
        if self.flames<=0:self.finish('lost','no_flames')
        elif self.time<=0:self.finish('lost','dawn')
        elif all(l['lit'] for l in self.lanterns):self.finish('won','all_lit')
    def finish(self,state,reason):
        self.state=state; self.score+=max(0,self.time//60)+self.flames*50; self.event('game_over',{'result':state,'reason':reason})
    def snapshot(self):
        return {'type':'snapshot','tick':self.tick,'sim_tick':self.tick,'state':self.state,'time_left_s':round(self.time/60,3),'score':self.score,'player':{'pos':[round(v,3) for v in self.player],'flames':self.flames,'carried':self.carried},'lanterns':[{'id':l['id'],'pos':l['pos'],'lit':l['lit'],'deposited':l['deposited']} for l in self.lanterns],'shades':[{'id':s['id'],'pos':[round(v,3) for v in s['pos']],'state':s['state']} for s in self.shades],'motes_active':len(self.motes)}

def run_headless(seed,ticks,every,scenario_path=None,inputs_path=None):
    sc=load_json(scenario_path,{})
    if not isinstance(sc,dict): raise ValueError('scenario must be an object')
    data=load_json(inputs_path,{'frames':[]})
    if not isinstance(data,dict) or not isinstance(data.get('frames',[]),list):raise ValueError('inputs.frames must be an array')
    frames=data.get('frames',[]); last=-1
    for f in frames:
        if not isinstance(f,dict) or not isinstance(f.get('tick'),int) or f['tick']<=last:raise ValueError('frame ticks must strictly increase')
        last=f['tick']
        if 'move' in f and (not isinstance(f['move'],list) or len(f['move'])!=2 or any(not isinstance(v,(int,float)) or abs(v)>1 for v in f['move'])):raise ValueError('move must contain two values in [-1,1]')
        for key in ('jump','interact','pulse'):
            if key in f and not isinstance(f[key],bool):raise ValueError(f'{key} must be boolean')
    g=Game(seed,sc); out=[json.dumps(g.snapshot(),separators=(',',':'))]; frame_i=0
    for k in range(ticks):
        while frame_i<len(frames) and frames[frame_i]['tick']==k:
            g.input.update(frames[frame_i]); frame_i+=1
        g.step()
        out.extend(json.dumps(e,separators=(',',':')) for e in g.events); g.events.clear()
        if g.tick%every==0:out.append(json.dumps(g.snapshot(),separators=(',',':')))
        if g.state!='playing':break
    out.append(json.dumps({'type':'end','ticks':g.tick,'state':g.state,'score':g.score},separators=(',',':')))
    return out
